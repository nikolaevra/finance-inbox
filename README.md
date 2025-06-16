# Finance Inbox

A comprehensive financial management application that helps you organize and process financial emails, invoices, and transactions automatically.

## 🚀 Features

- **Email Integration**: Connect with Gmail to fetch and process financial emails
- **Invoice Processing**: Automatically extract and categorize invoices
- **User Management**: Secure authentication with Clerk
- **Business Organization**: Support for multiple businesses and users
- **Database Management**: PostgreSQL with Alembic migrations
- **Modern Frontend**: React with Vite and Tailwind CSS

## 🏗️ Architecture

```
finance-inbox/
├── backend/                 # FastAPI backend
│   ├── services/           # Business logic services
│   ├── auth/              # Authentication modules
│   ├── models.py          # SQLAlchemy database models
│   ├── database.py        # Database configuration
│   ├── main.py           # FastAPI application
│   └── run.sh            # Backend startup script
├── frontend/              # React frontend
│   └── finance-inbox-frontend/
│       ├── src/          # React components
│       └── package.json  # Frontend dependencies
└── README.md             # This file
```

## 🛠️ Prerequisites

- **Python 3.9+**
- **Node.js 16+**
- **PostgreSQL** (installed via Homebrew on macOS)
- **Git**

## 📦 Installation

### 1. Clone the repository
```bash
git clone <repository-url>
cd finance-inbox
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install fastapi uvicorn sqlalchemy alembic psycopg2-binary python-dotenv

# Create .env file
cat > .env << EOF
DB_USER=nikolaevra
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=finance_inbox
EOF

# Create postgres user (if needed)
createuser -s postgres
```

### 3. Frontend Setup

```bash
cd frontend/finance-inbox-frontend

# Install dependencies
npm install
```

## 🚀 Running the Application

### Option 1: Using the provided scripts (Recommended)

#### Backend
```bash
cd backend
./run.sh
```

This script will:
- Start PostgreSQL automatically
- Create the database if it doesn't exist
- Run database migrations
- Start the FastAPI server on http://localhost:8000

#### Frontend
```bash
cd frontend/finance-inbox-frontend
npm run dev
```

The frontend will be available at http://localhost:5173

### Option 2: Manual startup

#### Backend
```bash
cd backend
source .venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend
```bash
cd frontend/finance-inbox-frontend
npm run dev
```

## 🗄️ Database Management

### Running Migrations
```bash
cd backend
python3 -m alembic upgrade head
```

### Creating New Migrations
```bash
cd backend
python3 -m alembic revision --autogenerate -m "Description of changes"
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the `backend/` directory:

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

### API Endpoints

- **Health Check**: `GET /health`
- **Root**: `GET /`
- **API Documentation**: `GET /docs` (Swagger UI)

## 🧪 Development

### Backend Development
- The backend uses FastAPI with automatic reload
- Database models are in `backend/models.py`
- Services are organized in `backend/services/`
- Run tests: `pytest` (when implemented)

### Frontend Development
- React with Vite for fast development
- Tailwind CSS for styling
- ESLint for code quality
- Run tests: `npm test` (when implemented)

## 📝 API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Run tests and ensure code quality
5. Commit your changes: `git commit -m 'Add feature'`
6. Push to the branch: `git push origin feature-name`
7. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Troubleshooting

### PostgreSQL Issues
- Ensure PostgreSQL is running: `brew services list`
- Start PostgreSQL: `brew services start postgresql@14`
- Create database: `createdb finance_inbox`

### Port Conflicts
- Backend runs on port 8000 by default
- Frontend runs on port 5173 by default
- Change ports in the respective configuration files if needed

### Python Environment
- Ensure you're using the virtual environment: `source .venv/bin/activate`
- Install missing packages: `pip install -r requirements.txt` (when available)

## 📞 Support

For issues and questions:
1. Check the troubleshooting section above
2. Review the API documentation at `/docs`
3. Create an issue in the repository