"""Gmail OAuth API endpoints."""

from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from services.google_service import GoogleService
from services.auth_service import get_current_user_profile
import logging
import os

logger = logging.getLogger(__name__)

# Get frontend URL from environment variable
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

router = APIRouter(prefix="/google-auth", tags=["Gmail OAuth"])

@router.get("/")
def login(current_user_profile: dict = Depends(get_current_user_profile)):
    """Get Google OAuth authorization URL for frontend to redirect to"""
    google_service = GoogleService(internal_user_id=current_user_profile["id"])
    # Include user ID in state parameter for callback identification
    authorization_url = google_service.get_authorization_url(state=current_user_profile["id"])
    return {
        "authorization_url": authorization_url,
        "message": "Use this URL to redirect user to Google OAuth"
    }

@router.get("/callback")
def oauth2callback(request: Request):
    """Handle Google OAuth callback and store tokens"""
    code = request.query_params.get("code")
    state = request.query_params.get("state")  # This contains the user ID
    
    if not code:
        return RedirectResponse(f"{FRONTEND_URL}/settings?error=no_code")
    
    if not state:
        return RedirectResponse(f"{FRONTEND_URL}/settings?error=no_state")
    
    try:
        # Use the user ID from state parameter
        google_service = GoogleService(internal_user_id=state)
        result = google_service.handle_oauth_callback(code)
        
        # Redirect back to frontend with success/error
        if "error" in result:
            return RedirectResponse(f"{FRONTEND_URL}/settings?error={result['error']}")
        else:
            return RedirectResponse(f"{FRONTEND_URL}/settings?success=gmail_connected")
            
    except Exception as e:
        logger.error(f"OAuth callback error: {str(e)}")
        return RedirectResponse(f"{FRONTEND_URL}/settings?error=callback_failed")

@router.get("/status")
def get_auth_status(current_user_profile: dict = Depends(get_current_user_profile)):
    """Check authentication status"""
    google_service = GoogleService(internal_user_id=current_user_profile["id"])
    return google_service.get_token_info()

@router.post("/logout")
def logout(current_user_profile: dict = Depends(get_current_user_profile)):
    """Clear stored tokens"""
    google_service = GoogleService(internal_user_id=current_user_profile["id"])
    return google_service.clear_tokens()

@router.get("/force-consent")
def force_consent(current_user_profile: dict = Depends(get_current_user_profile)):
    """Get authorization URL that forces consent screen (to get refresh token)"""
    google_service = GoogleService(internal_user_id=current_user_profile["id"])
    # This will use prompt='consent' to force the consent screen
    authorization_url = google_service.get_authorization_url()
    return {
        "authorization_url": authorization_url,
        "message": "This URL will force the consent screen to ensure you get a refresh token"
    } 