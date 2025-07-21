import os
import json
import yaml
import logging
from typing import Dict, Optional, Tuple
from datetime import datetime, timezone
from openai import OpenAI
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailCategorizationService:
    """Service for categorizing emails using OpenAI's API"""
    
    def __init__(self, user_id: str = None):
        # Validate OpenAI API key
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        # Try different initialization approaches
        try:
            # First try: basic initialization
            self.client = OpenAI(api_key=api_key)
        except Exception as e:
            raise Exception(f"Failed to initialize OpenAI client: {str(e)}")
        
        # Store user ID for user-specific prompt configuration
        self.user_id = user_id
        
        # Initialize configuration - will be loaded per-request if user_id is provided
        if user_id:
            # Load user-specific configuration from database
            self.config = self._load_user_config(user_id)
        else:
            # Load fallback YAML configuration
            self.config = self._load_yaml_config()
            
        self.prompt_version = self.config.get("prompt_version", "1.0")
        self.model = self.config.get("model", "gpt-3.5-turbo")
        self.temperature = self.config.get("temperature", 0.1)
        self.max_tokens = self.config.get("max_tokens", 200)
        self.timeout = self.config.get("timeout", 10)
        
    def _load_user_config(self, user_id: str) -> Dict:
        """Load user-specific prompt configuration from database"""
        try:
            from services.user_prompt_service import user_prompt_service
            config = user_prompt_service.get_user_prompt_config(user_id)
            logger.info(f"✅ Loaded user prompt config for {user_id}: v{config.get('prompt_version')}")
            return config
        except Exception as e:
            logger.warning(f"⚠️ Failed to load user config for {user_id}: {str(e)}")
            # Fallback to YAML config
            return self._load_yaml_config()
    
    def _load_yaml_config(self) -> Dict:
        """Load the fallback categorization configuration from YAML file"""
        config_path = Path(__file__).parent.parent / "prompts" / "email_categorization.yaml"
        
        if not config_path.exists():
            logger.warning(f"⚠️ YAML config file not found: {config_path}")
            return self._get_hardcoded_fallback()
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                
            # Validate required fields
            required_fields = ['template', 'model', 'prompt_version']
            missing_fields = [field for field in required_fields if not config.get(field)]
            
            if missing_fields:
                logger.warning(f"⚠️ Missing required fields in YAML config: {missing_fields}")
                return self._get_hardcoded_fallback()
                
            logger.info(f"✅ Loaded fallback YAML config: {config.get('name', 'unnamed')} v{config.get('prompt_version')}")
            return config
        except Exception as e:
            logger.warning(f"⚠️ Failed to load YAML config: {str(e)}")
            raise e
    
    def categorize_email(self, email_data: Dict, user_id: str = None) -> Tuple[Optional[str], Optional[float], Optional[str]]:
        """
        Categorize an email using OpenAI's API
        
        Args:
            email_data: Dictionary containing email information
            user_id: User ID for user-specific prompt configuration
            
        Returns:
            Tuple of (category, confidence, reasoning) or (None, None, None) if failed
        """
        try:
            # Get user-specific config if user_id is provided
            if user_id and user_id != self.user_id:
                config = self._load_user_config(user_id)
            else:
                config = self.config
                
            # Extract email content for categorization
            subject = email_data.get('subject', '')
            sender = email_data.get('from_email', '')
            snippet = email_data.get('snippet', '')
            body_text = email_data.get('body_text', '')
            
            # Use body_text if available, otherwise use snippet
            content = body_text if body_text else snippet
            # Limit content length to avoid excessive token usage
            content = content[:1000] + "..." if len(content) > 1000 else content
            
            # Format the prompt using the template and input variables
            template = config.get("template", "")
            prompt = template.format(
                subject=subject,
                sender=sender,
                content=content
            )
            
            logger.info(f"🤖 Categorizing email: {subject[:50]}...")
            
            # Make API call to OpenAI using configuration parameters
            response = self.client.chat.completions.create(
                model=config.get("model", "gpt-3.5-turbo"),
                messages=[
                    {"role": "system", "content": "You are an expert email categorization system for financial professionals."},
                    {"role": "user", "content": prompt}
                ],
                temperature=config.get("temperature", 0.1),
                max_tokens=config.get("max_tokens", 200),
                timeout=config.get("timeout", 10)
            )
            
            # Parse the response
            response_text = response.choices[0].message.content.strip()
            
            # Extract JSON from response
            try:
                # Try to find JSON in the response
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}') + 1
                
                if start_idx != -1 and end_idx != -1:
                    json_str = response_text[start_idx:end_idx]
                    result = json.loads(json_str)
                    
                    category = result.get('category')
                    confidence = result.get('confidence', 0.5)
                    reasoning = result.get('reasoning', '')
                    
                    logger.info(f"✅ Email categorized as: {category} (confidence: {confidence})")
                    return category, confidence, reasoning
                else:
                    logger.warning("⚠️ No JSON found in OpenAI response")
                    return None, None, None
                    
            except json.JSONDecodeError as e:
                logger.error(f"❌ Failed to parse JSON response: {str(e)}")
                logger.error(f"Response was: {response_text}")
                return None, None, None
                
        except Exception as e:
            logger.error(f"❌ Error categorizing email: {str(e)}")
            return None, None, None
    
    def categorize_email_with_metadata(self, email_data: Dict, user_id: str = None) -> Dict:
        """
        Categorize an email and return full metadata
        
        Args:
            email_data: Dictionary containing email information
            user_id: User ID for user-specific prompt configuration
            
        Returns:
            Dictionary with category, confidence, reasoning, and metadata
        """
        category, confidence, reasoning = self.categorize_email(email_data, user_id)
        
        # Get prompt version from config
        if user_id and user_id != self.user_id:
            config = self._load_user_config(user_id)
        else:
            config = self.config
            
        return {
            'category': category,
            'category_confidence': confidence,
            'categorized_at': datetime.now(timezone.utc),
            'category_prompt_version': str(config.get('prompt_version', '1.0')),
            'reasoning': reasoning
        }
    
    def get_valid_categories(self) -> list:
        """Get list of valid email categories"""
        return [
            'CLIENT_COMMUNICATION',
            'MARKET_RESEARCH', 
            'REGULATORY_COMPLIANCE',
            'FINANCIAL_REPORTING',
            'TRANSACTION_ALERTS',
            'INTERNAL_OPERATIONS',
            'VENDOR_SERVICES',
            'MARKETING_SALES',
            'EDUCATIONAL_CONTENT',
            'OTHER'
        ]
    
    def is_valid_category(self, category: str) -> bool:
        """Check if a category is valid"""
        return category in self.get_valid_categories()

    def batch_categorize_emails(self, supabase_client, user_id: str, limit: int = 50) -> Dict:
        """
        Batch categorize existing emails that don't have categories
        
        Args:
            supabase_client: Supabase client instance
            user_id: User ID to categorize emails for
            limit: Maximum number of emails to process in this batch
            
        Returns:
            Dictionary with batch processing results
        """
        try:
            logger.info(f"🔄 Starting batch categorization for user {user_id} (limit: {limit})")
            
            # Get emails that haven't been categorized yet
            result = supabase_client.table("emails").select("*").eq("user_id", user_id).is_("category", "null").limit(limit).execute()
            
            if not result.data:
                logger.info("✅ No uncategorized emails found")
                return {
                    "message": "No uncategorized emails found",
                    "processed": 0,
                    "successful": 0,
                    "failed": 0
                }
            
            emails_to_process = result.data
            logger.info(f"📧 Found {len(emails_to_process)} uncategorized emails to process")
            
            successful_count = 0
            failed_count = 0
            
            for email in emails_to_process:
                try:
                    # Categorize the email
                    categorization_result = self.categorize_email_with_metadata(email, user_id)
                    
                    if categorization_result['category']:
                        # Update the email with categorization data
                        update_data = {
                            'category': categorization_result['category'],
                            'category_confidence': categorization_result['category_confidence'],
                            'categorized_at': categorization_result['categorized_at'].isoformat(),
                            'category_prompt_version': categorization_result['category_prompt_version']
                        }
                        
                        # Update the email in database
                        supabase_client.table("emails").update(update_data).eq("id", email['id']).execute()
                        
                        successful_count += 1
                        logger.info(f"✅ Categorized email '{email.get('subject', 'No Subject')[:50]}...' as {categorization_result['category']}")
                    else:
                        failed_count += 1
                        logger.warning(f"⚠️ Failed to categorize email '{email.get('subject', 'No Subject')[:50]}...'")
                        
                except Exception as e:
                    failed_count += 1
                    logger.error(f"❌ Error categorizing email {email.get('id')}: {str(e)}")
            
            logger.info(f"✅ Batch categorization completed: {successful_count} successful, {failed_count} failed")
            
            return {
                "message": f"Batch categorization completed",
                "processed": len(emails_to_process),
                "successful": successful_count,
                "failed": failed_count
            }
            
        except Exception as e:
            logger.error(f"❌ Error in batch categorization: {str(e)}")
            return {
                "error": f"Batch categorization failed: {str(e)}",
                "processed": 0,
                "successful": 0,
                "failed": 0
            }

# Global instance - will be initialized when first accessed
email_categorization_service = None

def get_email_categorization_service() -> EmailCategorizationService:
    """Get or create the email categorization service instance"""
    global email_categorization_service
    
    if email_categorization_service is None:
        try:
            email_categorization_service = EmailCategorizationService()
        except Exception as e:
            logger.error(f"❌ Failed to initialize email categorization service: {str(e)}")
            raise e
    
    return email_categorization_service 