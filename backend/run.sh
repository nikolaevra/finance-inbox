#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if PostgreSQL is running
check_postgres() {
    if pg_isready -q; then
        return 0
    else
        return 1
    fi
}

# Function to start PostgreSQL
start_postgres() {
    print_status "Checking PostgreSQL status..."
    
    if check_postgres; then
        print_success "PostgreSQL is already running"
        return 0
    fi
    
    print_status "Starting PostgreSQL..."
    
    # Try different methods to start PostgreSQL
    if command -v brew &> /dev/null; then
        # macOS with Homebrew
        brew services start postgresql@14 2>/dev/null || brew services start postgresql 2>/dev/null
    elif command -v systemctl &> /dev/null; then
        # Linux with systemd
        sudo systemctl start postgresql
    elif command -v service &> /dev/null; then
        # Linux with service
        sudo service postgresql start
    else
        print_error "Could not start PostgreSQL automatically. Please start it manually."
        return 1
    fi
    
    # Wait for PostgreSQL to be ready
    print_status "Waiting for PostgreSQL to be ready..."
    for i in {1..30}; do
        if check_postgres; then
            print_success "PostgreSQL is ready"
            return 0
        fi
        sleep 1
    done
    
    print_error "PostgreSQL failed to start within 30 seconds"
    return 1
}

# Function to create database if it doesn't exist
create_database() {
    # Use system username for Homebrew PostgreSQL, fallback to postgres
    local db_name=${DB_NAME:-finance_inbox}
    local db_user=${DB_USER:-$(whoami)}
    
    print_status "Checking if database '$db_name' exists..."
    
    if psql -U "$db_user" -lqt | cut -d \| -f 1 | grep -qw "$db_name"; then
        print_success "Database '$db_name' already exists"
    else
        print_status "Creating database '$db_name'..."
        createdb -U "$db_user" "$db_name"
        if [ $? -eq 0 ]; then
            print_success "Database '$db_name' created successfully"
        else
            print_error "Failed to create database '$db_name'"
            return 1
        fi
    fi
}

# Function to run database migrations
run_migrations() {
    print_status "Running database migrations..."
    
    if command -v alembic &> /dev/null; then
        python3 -m alembic upgrade head
        if [ $? -eq 0 ]; then
            print_success "Migrations completed successfully"
        else
            print_error "Migration failed"
            return 1
        fi
    else
        print_warning "Alembic not found, skipping migrations"
    fi
}

# Function to start the FastAPI server
start_server() {
    print_status "Starting FastAPI server..."
    
    # Check if required packages are installed
    if ! python3 -c "import fastapi, uvicorn" 2>/dev/null; then
        print_error "Required packages not found. Please install them with: pip install fastapi uvicorn"
        return 1
    fi
    
    # Start the server
    print_success "Server starting on http://localhost:8000"
    print_status "Press Ctrl+C to stop the server"
    
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
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
        print_warning "No .env file found. Using default database configuration."
    fi
    
    # Start PostgreSQL
    if ! start_postgres; then
        print_error "Failed to start PostgreSQL. Exiting."
        exit 1
    fi
    
    # Create database
    if ! create_database; then
        print_error "Failed to create database. Exiting."
        exit 1
    fi
    
    # Run migrations
    if ! run_migrations; then
        print_error "Failed to run migrations. Exiting."
        exit 1
    fi
    
    # Start server
    start_server
}

# Run the main function
main 