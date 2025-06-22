"""Inbox API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from services.google_service import GoogleService
from services.auth_service import get_current_user_profile
from services.connections_service import connections_service
from models import ConnectionProvider
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/inbox", tags=["Inbox"])

@router.get("/")
def get_inbox(limit: int = 50, offset: int = 0, current_user_profile: dict = Depends(get_current_user_profile)):
    """Get user's inbox - all stored emails from database"""
    google_service = GoogleService(internal_user_id=current_user_profile["id"])
    emails = google_service.get_inbox_emails(limit=limit, offset=offset)
    return {
        "inbox": emails,
        "count": len(emails),
        "limit": limit,
        "offset": offset,
        "source": "database"
    }

@router.post("/emails/sync")
def sync_emails(max_results: int = 50, current_user_profile: dict = Depends(get_current_user_profile)):
    """Fetch emails from Gmail and store them in database"""
    google_service = GoogleService(internal_user_id=current_user_profile["id"])
    emails = google_service.fetch_gmail_emails(max_results=max_results)
    return {
        "message": f"Successfully synced {len(emails)} emails",
        "emails_synced": len(emails),
        "source": "gmail_api"
    }

@router.get("/email/{email_id}")
def get_single_email(email_id: str, current_user_profile: dict = Depends(get_current_user_profile)):
    """Get detailed information for a single email from database"""
    google_service = GoogleService(internal_user_id=current_user_profile["id"])
    email = google_service.get_single_email_from_db(email_id)
    
    if not email:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Email with ID {email_id} not found"
        )
    
    return email

@router.get("/connections")
def get_user_connections(current_user_profile: dict = Depends(get_current_user_profile)):
    """Get all user connections with their status"""
    connections = connections_service.get_user_connections(current_user_profile["id"])
    return {
        "connections": connections,
        "count": len(connections)
    }

@router.post("/connections/{provider}/disconnect")
def disconnect_provider(provider: str, current_user_profile: dict = Depends(get_current_user_profile)):
    """Disconnect a specific provider"""
    # Validate provider
    try:
        connection_provider = ConnectionProvider(provider.lower())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid provider: {provider}. Supported providers: gmail"
        )
    
    # Handle Gmail disconnection
    if connection_provider == ConnectionProvider.GMAIL:
        # Use GoogleService to clear tokens and disconnect
        google_service = GoogleService(internal_user_id=current_user_profile["id"])
        result = google_service.clear_tokens()
        return {
            "message": f"Successfully disconnected from {provider}",
            "provider": provider,
            "details": result
        }
    
    # For other providers, just update status
    success = connections_service.disconnect_provider(
        user_id=current_user_profile["id"],
        provider=connection_provider
    )
    
    if success:
        return {
            "message": f"Successfully disconnected from {provider}",
            "provider": provider
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active connection found for {provider}"
        )
