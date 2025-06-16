# Finance Inbox Backend

FastAPI backend for the Finance Inbox application with PostgreSQL database, Alembic migrations, and Gmail integration.

## 🏗️ Architecture

```
backend/
├── services/              # Business logic services
│   ├── google_auth.py    # Google OAuth authentication
│   ├── gmail.py          # Gmail API integration
│   └── __init__.py
├── auth/                 # Authentication modules
├── migrations/           # Alembic database migrations
├── models.py            # SQLAlchemy database models
├── database.py          # Database configuration
├── main.py             # FastAPI application entry point
├── run.sh              # Automated startup script
├── alembic.ini         # Alembic configuration
└── README.md           # This file
```

## 🛠️ Prerequisites

- **Python 3.9+**
- **PostgreSQL** (installed via Homebrew on macOS)
- **pip** (Python package manager)

## 📦 Installation

### 1. Create Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install fastapi uvicorn sqlalchemy alembic psycopg2-binary python-dotenv
```

### 3. Database Setup
```bash
# Create postgres user (if needed)
createuser -s postgres

# Create database
createdb finance_inbox
```

### 4. Environment Configuration
Create a `.env` file in the backend directory:
```bash
# Database Configuration
DB_USER=nikolaevra
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=finance_inbox

# Other configuration
DEBUG=True
```

## 🚀 Running the Application

### Option 1: Using the Automated Script (Recommended)
```bash
./run.sh
```

This script will:
- ✅ Start PostgreSQL automatically
- ✅ Create the database if it doesn't exist
- ✅ Run database migrations
- ✅ Start the FastAPI server on http://localhost:8000

### Option 2: Manual Startup
```bash
# Activate virtual environment
source .venv/bin/activate

# Run migrations
python3 -m alembic upgrade head

# Start the server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 🗄️ Database Management

### Models
The application uses SQLAlchemy ORM with the following models:

- **User**: User accounts with Clerk integration
- **Business**: Business entities that users belong to

### Running Migrations
```bash
# Apply all pending migrations
python3 -m alembic upgrade head

# Create a new migration
python3 -m alembic revision --autogenerate -m "Description of changes"

# Downgrade to a specific revision
python3 -m alembic downgrade <revision_id>
```

### Database Connection
The application uses PostgreSQL with the following configuration:
- **Host**: localhost (configurable via DB_HOST)
- **Port**: 5432 (configurable via DB_PORT)
- **Database**: finance_inbox (configurable via DB_NAME)
- **User**: nikolaevra (configurable via DB_USER)

## 🔧 API Endpoints

### Health & Status
- `GET /` - Root endpoint
- `GET /health` - Health check

### Authentication (via services)
- Google OAuth integration
- Clerk user management

### Gmail Integration
- Email fetching and processing
- Invoice extraction

## 🧪 Development

### Code Structure
- **`main.py`**: FastAPI application setup and routing
- **`models.py`**: SQLAlchemy database models
- **`database.py`**: Database connection and session management
- **`services/`**: Business logic and external API integrations

### Adding New Endpoints
1. Create your route in `main.py` or a separate router file
2. Add any required models to `models.py`
3. Create migrations if database changes are needed
4. Update this README with new endpoint documentation

### Environment Variables
The application uses the following environment variables:
- `DB_USER`: PostgreSQL username
- `DB_PASSWORD`: PostgreSQL password
- `DB_HOST`: PostgreSQL host
- `DB_PORT`: PostgreSQL port
- `DB_NAME`: PostgreSQL database name

## 📝 API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🆘 Troubleshooting

### PostgreSQL Issues
```bash
# Check if PostgreSQL is running
brew services list

# Start PostgreSQL
brew services start postgresql@14

# Check connection
pg_isready
```

### Migration Issues
```bash
# Reset migrations (DANGER: This will delete all data)
python3 -m alembic downgrade base
python3 -m alembic upgrade head
```

### Port Conflicts
If port 8000 is in use, change it in the uvicorn command:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

### Virtual Environment Issues
```bash
# Recreate virtual environment
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt  # if available
```

## 🔒 Security

- Environment variables for sensitive configuration
- SQLAlchemy parameterized queries to prevent SQL injection
- CORS middleware configured for frontend integration

## 📊 Monitoring

- Health check endpoint for monitoring
- Structured logging (can be enhanced)
- Error handling with appropriate HTTP status codes

## 🚀 Deployment

For production deployment:
1. Set `DEBUG=False` in environment variables
2. Use a production WSGI server (Gunicorn)
3. Configure proper CORS origins
4. Set up proper database credentials
5. Enable HTTPS

## 📞 Support

For backend-specific issues:
1. Check the troubleshooting section above
2. Review the API documentation at `/docs`
3. Check the logs for error messages
4. Create an issue in the repository 