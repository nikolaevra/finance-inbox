#!/usr/bin/env python3
"""
Standalone script to categorize existing emails using LLM

This script finds all emails in the database that don't have categories
and processes them in batches using the email categorization service.

Usage:
    python categorize_existing_emails.py [--batch-size 50] [--user-id UUID]
"""

import os
import sys
import argparse
import time
from pathlib import Path
from typing import Optional

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def main():
    """Main function to categorize existing emails"""
    parser = argparse.ArgumentParser(
        description="Categorize existing emails that don't have categories"
    )
    parser.add_argument(
        "--batch-size", 
        type=int, 
        default=50, 
        help="Number of emails to process in each batch (default: 50)"
    )
    parser.add_argument(
        "--user-id", 
        type=str, 
        help="Specific user ID to process (optional, processes all users if not specified)"
    )
    parser.add_argument(
        "--delay", 
        type=float, 
        default=1.0, 
        help="Delay between batches in seconds (default: 1.0)"
    )
    parser.add_argument(
        "--dry-run", 
        action="store_true", 
        help="Show what would be processed without actually categorizing"
    )
    
    args = parser.parse_args()
    
    print("🚀 Email Categorization Script")
    print("=" * 50)
    
    # Validate environment
    if not validate_environment():
        sys.exit(1)
    
    try:
        # Import services after path setup
        from services.email_categorization_service import get_email_categorization_service
        from database import get_supabase
        
        # Initialize services
        print("🔧 Initializing services...")
        categorization_service = get_email_categorization_service()
        supabase = get_supabase()
        
        print(f"✅ Services initialized successfully!")
        print(f"   - Model: {categorization_service.model}")
        print(f"   - Temperature: {categorization_service.temperature}")
        print(f"   - Prompt Version: {categorization_service.prompt_version}")
        
        # Get uncategorized emails count
        total_uncategorized = get_uncategorized_count(supabase, args.user_id)
        
        if total_uncategorized == 0:
            print("\n✅ No uncategorized emails found!")
            return
        
        print(f"\n📊 Found {total_uncategorized} uncategorized emails")
        print(f"   - Batch size: {args.batch_size}")
        print(f"   - Estimated batches: {(total_uncategorized + args.batch_size - 1) // args.batch_size}")
        print(f"   - User filter: {args.user_id or 'All users'}")
        
        if args.dry_run:
            print("\n🔍 DRY RUN MODE - No actual categorization will be performed")
            return
        
        # Confirm before proceeding
        response = input(f"\nProceed with categorization? (y/N): ")
        if response.lower() != 'y':
            print("❌ Categorization cancelled")
            return
        
        # Process in batches
        print(f"\n🤖 Starting categorization...")
        start_time = time.time()
        
        total_processed = 0
        total_successful = 0
        total_failed = 0
        batch_num = 1
        
        while True:
            print(f"\n📦 Processing batch {batch_num}...")
            
            # Process batch
            result = categorization_service.batch_categorize_emails(
                supabase_client=supabase,
                user_id=args.user_id,
                limit=args.batch_size
            )
            
            # Update counters
            batch_processed = result.get("processed", 0)
            batch_successful = result.get("successful", 0)
            batch_failed = result.get("failed", 0)
            
            total_processed += batch_processed
            total_successful += batch_successful
            total_failed += batch_failed
            
            # Show batch results
            print(f"   ✅ Processed: {batch_processed}")
            print(f"   ✅ Successful: {batch_successful}")
            print(f"   ❌ Failed: {batch_failed}")
            
            # Check if we're done
            if batch_processed == 0:
                print("   🏁 No more emails to process")
                break
            
            # Show progress
            progress = (total_processed / total_uncategorized) * 100
            print(f"   📈 Progress: {total_processed}/{total_uncategorized} ({progress:.1f}%)")
            
            # Check for errors
            if "error" in result:
                print(f"   ⚠️ Batch error: {result['error']}")
            
            batch_num += 1
            
            # Delay between batches to avoid overwhelming the API
            if args.delay > 0 and batch_processed > 0:
                print(f"   ⏸️ Waiting {args.delay}s before next batch...")
                time.sleep(args.delay)
        
        # Final statistics
        elapsed_time = time.time() - start_time
        print(f"\n🎉 Categorization completed!")
        print(f"   - Total processed: {total_processed}")
        print(f"   - Successful: {total_successful}")
        print(f"   - Failed: {total_failed}")
        print(f"   - Success rate: {(total_successful/total_processed*100) if total_processed > 0 else 0:.1f}%")
        print(f"   - Time elapsed: {elapsed_time:.1f}s")
        print(f"   - Average per email: {(elapsed_time/total_processed) if total_processed > 0 else 0:.2f}s")
        
    except KeyboardInterrupt:
        print(f"\n⏹️ Categorization interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during categorization: {str(e)}")
        sys.exit(1)

def validate_environment() -> bool:
    """Validate that required environment variables and dependencies are available"""
    print("🔍 Validating environment...")
    
    # Check OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY environment variable is required")
        print("   Set it with: export OPENAI_API_KEY='your-api-key'")
        return False
    
    # Check required files
    config_file = backend_dir / "prompts" / "email_categorization.yaml"
    if not config_file.exists():
        print(f"❌ Configuration file not found: {config_file}")
        return False
    
    print("✅ Environment validation passed")
    return True

def get_uncategorized_count(supabase, user_id: Optional[str] = None) -> int:
    """Get count of emails that don't have categories"""
    try:
        query = supabase.table("emails").select("id", count="exact").is_("category", "null")
        
        if user_id:
            query = query.eq("user_id", user_id)
        
        result = query.execute()
        return result.count or 0
        
    except Exception as e:
        print(f"❌ Error getting uncategorized email count: {str(e)}")
        return 0

if __name__ == "__main__":
    main() 