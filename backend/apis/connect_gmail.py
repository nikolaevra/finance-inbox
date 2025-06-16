from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from services.google_service import GoogleService

router = APIRouter()
google_service = GoogleService()

# Step 1: Send user to Google login
@router.get("/google-auth")
def login():
    """Redirect user to Google OAuth login"""
    authorization_url = google_service.get_authorization_url()
    return RedirectResponse(authorization_url)

# Step 2: Handle Google OAuth callback
@router.get("/google-auth/callback")
def oauth2callback(request: Request):
    """Handle Google OAuth callback and store tokens"""
    code = request.query_params.get("code")
    result = google_service.handle_oauth_callback(code)
    return result

# Step 3: Get user emails
@router.get("/fetch-emails")
def get_emails():
    """Fetch user's Gmail emails"""
    emails = google_service.fetch_gmail_emails()
    return emails

# Additional utility endpoints
@router.get("/google-auth/status")
def get_auth_status():
    """Check authentication status"""
    return {
        "authenticated": google_service.is_authenticated(),
        "has_tokens": bool(google_service.get_tokens())
    }

@router.post("/google-auth/logout")
def logout():
    """Clear stored tokens"""
    return google_service.clear_tokens() 