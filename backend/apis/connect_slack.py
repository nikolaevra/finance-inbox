"""Slack OAuth API endpoints."""

from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from services.slack_service import SlackService
from services.auth_service import get_current_user_profile
import logging
import os

logger = logging.getLogger(__name__)

# Get frontend URL from environment variable
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

router = APIRouter(prefix="/slack-auth", tags=["Slack OAuth"])

@router.get("/")
def login(current_user_profile: dict = Depends(get_current_user_profile)):
    """Get Slack OAuth authorization URL for frontend to redirect to"""
    slack_service = SlackService(internal_user_id=current_user_profile["id"])
    # Include user ID in state parameter for callback identification
    authorization_url = slack_service.get_authorization_url(state=current_user_profile["id"])
    return {
        "authorization_url": authorization_url,
        "message": "Use this URL to redirect user to Slack OAuth"
    }

@router.get("/callback")
def oauth2callback(request: Request):
    """Handle Slack OAuth callback and store tokens"""
    code = request.query_params.get("code")
    state = request.query_params.get("state")  # This contains the user ID

    logger.info(f"OAuth callback received: code={code}, state={state}")
    
    if not code:
        return RedirectResponse(f"{FRONTEND_URL}/settings?error=no_code")
    
    if not state:
        return RedirectResponse(f"{FRONTEND_URL}/settings?error=no_state")
    
    try:
        # Use the user ID from state parameter
        slack_service = SlackService(internal_user_id=state)
        result = slack_service.handle_oauth_callback(code)
        
        # Redirect back to frontend with success/error
        if "error" in result:
            return RedirectResponse(f"{FRONTEND_URL}/settings?error={result['error']}")
        else:
            return RedirectResponse(f"{FRONTEND_URL}/settings?success=slack_connected")
            
    except Exception as e:
        logger.error(f"OAuth callback error: {str(e)}")
        return RedirectResponse(f"{FRONTEND_URL}/settings?error=callback_failed")

@router.get("/status")
def get_auth_status(current_user_profile: dict = Depends(get_current_user_profile)):
    """Get Slack authentication status for current user"""
    try:
        slack_service = SlackService(internal_user_id=current_user_profile["id"])
        
        # Test if we have a valid token
        has_valid_token = slack_service.get_valid_token() is not None
        
        if has_valid_token:
            # Test the connection
            connection_works = slack_service.test_connection()
            return {
                "authenticated": True,
                "connection_status": "connected" if connection_works else "error"
            }
        else:
            return {
                "authenticated": False,
                "connection_status": "disconnected"
            }
            
    except Exception as e:
        logger.error(f"Error checking Slack auth status: {str(e)}")
        return {
            "authenticated": False,
            "connection_status": "error",
            "error": str(e)
        }

@router.delete("/disconnect")
def disconnect(current_user_profile: dict = Depends(get_current_user_profile)):
    """Disconnect Slack integration for current user"""
    try:
        from services.connections_service import connections_service
        from models import ConnectionProvider
        
        success = connections_service.disconnect_provider(
            user_id=current_user_profile["id"],
            provider=ConnectionProvider.SLACK
        )
        
        if success:
            return {"message": "Slack disconnected successfully"}
        else:
            return {"error": "Failed to disconnect Slack"}
            
    except Exception as e:
        logger.error(f"Error disconnecting Slack: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to disconnect Slack"
        ) 