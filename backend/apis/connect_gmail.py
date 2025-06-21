from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import RedirectResponse
from services.google_service import GoogleService
from services.auth_service import get_current_user
from uuid import UUID, uuid4

router = APIRouter()

@router.get("/fetch-emails")
def get_emails(max_results: int = 10, current_user: dict = Depends(get_current_user)):
    """Fetch user's Gmail emails with full content"""
    google_service = GoogleService(user_id=current_user["user_id"])
    emails = google_service.fetch_gmail_emails(max_results=max_results)
    return {"emails": emails, "count": len(emails)}

@router.get("/email/{email_id}")
def get_single_email(email_id: str, current_user: dict = Depends(get_current_user)):
    """Get detailed information for a single email from Gmail"""
    google_service = GoogleService(user_id=current_user["user_id"])
    email = google_service.get_single_email(email_id)
    return email

@router.get("/inbox")
def get_inbox(limit: int = 50, offset: int = 0, current_user: dict = Depends(get_current_user)):
    """Get user's inbox - all stored emails from database"""
    google_service = GoogleService(user_id=current_user["user_id"])
    emails = google_service.get_inbox_emails(limit=limit, offset=offset)
    return {
        "inbox": emails,
        "count": len(emails),
        "limit": limit,
        "offset": offset,
        "source": "database"
    }

@router.get("/emails/stored")
def get_stored_emails(limit: int = 20, current_user: dict = Depends(get_current_user)):
    """Get emails from database (previously fetched and stored)"""
    google_service = GoogleService(user_id=current_user["user_id"])
    emails = google_service._get_emails_from_db(limit=limit)
    return {"emails": emails, "count": len(emails), "source": "database"}

@router.post("/emails/sync")
def sync_emails(max_results: int = 50, current_user: dict = Depends(get_current_user)):
    """Fetch emails from Gmail and store them in database"""
    google_service = GoogleService(user_id=current_user["user_id"])
    emails = google_service.fetch_gmail_emails(max_results=max_results)
    return {
        "message": f"Successfully synced {len(emails)} emails",
        "emails_synced": len(emails),
        "source": "gmail_api"
    }

@router.get("/google-auth")
def login(current_user: dict = Depends(get_current_user)):
    """Redirect user to Google OAuth login"""
    google_service = GoogleService(user_id=current_user["user_id"])
    authorization_url = google_service.get_authorization_url()
    return RedirectResponse(authorization_url)

@router.get("/google-auth/callback")
def oauth2callback(request: Request, current_user: dict = Depends(get_current_user)):
    """Handle Google OAuth callback and store tokens"""
    google_service = GoogleService(user_id=current_user["user_id"])
    code = request.query_params.get("code")
    result = google_service.handle_oauth_callback(code)
    return result

# Additional utility endpoints
@router.get("/google-auth/status")
def get_auth_status(current_user: dict = Depends(get_current_user)):
    """Check authentication status"""
    google_service = GoogleService(user_id=current_user["user_id"])
    return google_service.get_token_info()

@router.post("/google-auth/logout")
def logout(current_user: dict = Depends(get_current_user)):
    """Clear stored tokens"""
    google_service = GoogleService(user_id=current_user["user_id"])
    return google_service.clear_tokens()

@router.get("/google-auth/force-consent")
def force_consent(current_user: dict = Depends(get_current_user)):
    """Get authorization URL that forces consent screen (to get refresh token)"""
    google_service = GoogleService(user_id=current_user["user_id"])
    # This will use prompt='consent' to force the consent screen
    authorization_url = google_service.get_authorization_url()
    return {
        "authorization_url": authorization_url,
        "message": "This URL will force the consent screen to ensure you get a refresh token"
    } 