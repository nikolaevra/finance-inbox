from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse
from services.google_service import GoogleService
from uuid import UUID, uuid4

router = APIRouter()

# For demo purposes, we'll use a hardcoded user ID
# In production, you'd get this from authentication middleware
DEMO_USER_ID = "3c1415b3-245f-4140-a70b-306e18549ab1"  # This would come from your auth system


@router.get("/fetch-emails")
def get_emails():
    """Fetch user's Gmail emails"""
    google_service = GoogleService(user_id=DEMO_USER_ID)
    emails = google_service.fetch_gmail_emails()
    return emails

@router.get("/google-auth")
def login():
    """Redirect user to Google OAuth login"""
    google_service = GoogleService(user_id=DEMO_USER_ID)
    authorization_url = google_service.get_authorization_url()
    return RedirectResponse(authorization_url)

@router.get("/google-auth/callback")
def oauth2callback(request: Request):
    """Handle Google OAuth callback and store tokens"""
    google_service = GoogleService(user_id=DEMO_USER_ID)
    code = request.query_params.get("code")
    result = google_service.handle_oauth_callback(code)
    return result

# Additional utility endpoints
@router.get("/google-auth/status")
def get_auth_status():
    """Check authentication status"""
    google_service = GoogleService(user_id=DEMO_USER_ID)
    return google_service.get_token_info()

@router.post("/google-auth/logout")
def logout():
    """Clear stored tokens"""
    google_service = GoogleService(user_id=DEMO_USER_ID)
    return google_service.clear_tokens()

@router.get("/google-auth/force-consent")
def force_consent():
    """Get authorization URL that forces consent screen (to get refresh token)"""
    google_service = GoogleService(user_id=DEMO_USER_ID)
    # This will use prompt='consent' to force the consent screen
    authorization_url = google_service.get_authorization_url()
    return {
        "authorization_url": authorization_url,
        "message": "This URL will force the consent screen to ensure you get a refresh token"
    } 