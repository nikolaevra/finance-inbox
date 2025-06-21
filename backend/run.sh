#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check database connection
check_database() {
    print_status "Checking database connection..."
    
    # Simple check - just verify environment variables are set
    if [ -z "$SUPABASE_URL" ] || [ -z "$SUPABASE_KEY" ]; then
        print_error "SUPABASE_URL and SUPABASE_KEY must be set in .env file"
        return 1
    fi
    
    print_success "Database configuration looks good"
    return 0
}

# Function to start the FastAPI server
start_server() {
    print_status "Starting FastAPI server..."
    
    # Check if required packages are installed
    if ! python3 -c "import fastapi, uvicorn, supabase" 2>/dev/null; then
        print_error "Required packages not found. Please install them with: pip install fastapi uvicorn supabase"
        return 1
    fi
    
    print_success "Server starting on http://localhost:8000"
    print_status "Press Ctrl+C to stop the server"
    
    python3 -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
}

# Function to cleanup on exit
cleanup() {
    print_status "Shutting down..."
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Main execution
main() {
    echo "========================================"
    echo "    Finance Inbox Backend Runner"
    echo "========================================"
    echo ""
    
    # Load environment variables
    if [ -f .env ]; then
        print_status "Loading environment variables from .env"
        export $(cat .env | grep -v '^#' | xargs)
    else
        print_error "No .env file found. Please create one with your Supabase credentials."
        exit 1
    fi
    
    # Check database configuration
    if ! check_database; then
        print_error "Database configuration check failed. Exiting."
        exit 1
    fi
    
    # Start server
    start_server
}

# Run the main function
main

