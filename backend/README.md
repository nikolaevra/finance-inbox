# Finance Inbox Backend

FastAPI backend for the Finance Inbox application with Supabase authentication, database integration, and Gmail connectivity.

## 🏗️ Architecture

```
backend/
├── services/              # Business logic services
│   ├── auth_service.py   # Supabase authentication service
│   ├── google_service.py # Google OAuth & Gmail integration
│   └── __init__.py
├── apis/                 # API route handlers
│   ├── auth.py          # Authentication endpoints
│   ├── connect_gmail.py # Gmail API endpoints
│   └── __init__.py
├── supabase/            # Database migrations
│   └── migrations/      # SQL migration files
├── models.py           # SQLAlchemy database models
├── database.py         # Supabase client configuration
├── main.py            # FastAPI application entry point
├── run.sh             # Automated startup script
└── README.md          # This file
```

## 🛠️ Prerequisites

- **Python 3.9+**
- **Supabase account with Auth enabled**
- **Google Cloud Console project with Gmail API enabled**
- **pip** (Python package manager)

## 📦 Installation

### 1. Create Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Supabase Configuration
1. Create a project in Supabase
2. Enable Authentication in your Supabase project
3. Note down the following from your project settings:
   - Project URL
   - Service role key
   - JWT Secret (from API settings)

### 4. Environment Configuration
Create a `.env` file in the backend directory:
```bash
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_service_role_key
SUPABASE_JWT_SECRET=your_jwt_secret

# Other configuration
DEBUG=True
```

**⚠️ Important**: The `SUPABASE_JWT_SECRET` is required for token verification and can be found in your Supabase project settings under API → JWT Settings.

## 🔐 Authentication System

The application uses **Supabase Auth** with a streamlined client-side approach:

### Features
- **Client-Side Authentication**: Frontend uses Supabase client for signup/signin
- **JWT Token Verification**: Backend verifies JWT tokens for protected routes
- **Automatic Profile Creation**: Database trigger creates user profiles on signup
- **User Data Isolation**: All data isolated per authenticated user

### Authentication Flow
```
1. Frontend → Supabase Auth (signup/signin)
2. Supabase → Returns JWT token to frontend
3. Database trigger → Automatically creates user profile
4. Frontend → Includes JWT in API requests
5. Backend → Verifies JWT and processes requests
```

### API Endpoints

#### Authentication Endpoints
- `POST /auth/login` - Login with email/password (backup endpoint)
- `POST /auth/refresh` - Refresh access token
- `POST /auth/logout` - Logout current user
- `GET /auth/me` - Get current user info
- `GET /auth/profile` - Get user profile details

#### Protected Endpoints (Auth Required)
All Gmail endpoints require a valid JWT token in the Authorization header:
```bash
Authorization: Bearer <your_jwt_token>
```

- `GET /inbox` - Get user's emails
- `POST /emails/sync` - Sync Gmail emails
- All Gmail integration endpoints

### Frontend Integration
The frontend:
1. Uses Supabase client for authentication
2. Stores JWT tokens securely
3. Includes tokens in API requests: `Authorization: Bearer <token>`
4. Handles token refresh automatically

## 🚀 Running the Application

### Option 1: Using the Automated Script (Recommended)
```bash
./run.sh
```

### Option 2: Manual Startup
```bash
# Activate virtual environment
source .venv/bin/activate

# Start the server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The server will start on http://localhost:8000

## 🗄️ Database Management

### Database Schema
The application uses Supabase with the following tables:

- **auth.users**: Supabase managed user accounts
- **users**: Extended user profiles (auto-created via trigger)
- **businesses**: Business entities
- **oauth_tokens**: Google OAuth tokens per user
- **emails**: Stored email data
- **email_attachments**: Email attachment metadata

### Automatic Profile Creation
When users sign up through Supabase Auth:
1. ✅ Supabase creates record in `auth.users`
2. ✅ Database trigger automatically creates profile in `public.users`
3. ✅ User can immediately access protected endpoints

### Migrations
Database migrations are managed through Supabase:
1. Navigate to your Supabase project
2. Go to SQL Editor
3. Run migration files from `/supabase/migrations/`

## 🔧 API Endpoints

### Health & Status
- `GET /` - Root endpoint
- `GET /health` - Health check

### Authentication
- `POST /auth/login` - Login (backup endpoint)
- `POST /auth/refresh` - Refresh token
- `POST /auth/logout` - Logout
- `GET /auth/me` - Get current user

### Gmail Integration (Authenticated)
- `GET /inbox` - Get stored emails
- `POST /emails/sync` - Sync from Gmail
- `GET /google-auth` - Start Google OAuth
- `GET /google-auth/callback` - OAuth callback
- `GET /google-auth/status` - Check OAuth status

## 🧪 Development

### Testing Authentication
Since the frontend handles authentication, test by:
1. Using the frontend to sign up/login
2. Getting the JWT token from browser dev tools
3. Using the token in API requests:
   ```bash
   curl -H "Authorization: Bearer <your_token>" http://localhost:8000/inbox
   ```

### Code Structure
- **`services/auth_service.py`**: JWT token verification and user management
- **`apis/auth.py`**: Authentication route handlers  
- **`main.py`**: FastAPI app with auth middleware
- **`database.py`**: Supabase client configuration

### Adding Protected Endpoints
```python
from services.auth_service import get_current_user

@router.get("/protected-endpoint")
async def protected_route(current_user: dict = Depends(get_current_user)):
    user_id = current_user["user_id"]
    # Your protected logic here
```

### Environment Variables
Required environment variables:
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_KEY`: Service role key for database operations
- `SUPABASE_JWT_SECRET`: JWT secret for token verification

## 📝 API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔒 Security Features

- **JWT Token Authentication**: Secure user authentication
- **Database Triggers**: Automatic user profile creation
- **Row Level Security**: Database-level data isolation
- **User Data Isolation**: All data scoped to authenticated users
- **CORS Configuration**: Configured for frontend integration
- **Environment Variables**: Sensitive data in environment variables

## 🆘 Troubleshooting

### Authentication Issues
- Verify `SUPABASE_JWT_SECRET` is correct
- Check Supabase Auth is enabled in your project
- Ensure tokens are included in request headers

### Profile Issues
- Check database trigger is working: `public.handle_new_user()`
- Verify RLS policies are not blocking profile creation
- Check migration was applied successfully

### Supabase Connection Issues
- Verify your Supabase project URL and keys
- Check project status in Supabase dashboard
- Ensure service role key has proper permissions

### Gmail Integration Issues
- Verify Google Cloud Console setup
- Check OAuth credentials configuration
- Ensure Gmail API is enabled

## 🚀 Deployment

For production deployment:
1. Set proper environment variables
2. Configure CORS for your frontend domain
3. Use HTTPS for security
4. Set up proper database credentials
5. Enable rate limiting

## 📞 Support

For backend-specific issues:
1. Check the troubleshooting section above
2. Review the API documentation at `/docs`
3. Check the logs for error messages
4. Verify environment variable configuration 