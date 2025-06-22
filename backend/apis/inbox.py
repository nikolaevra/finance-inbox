"""Inbox API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from services.google_service import GoogleService
from services.auth_service import get_current_user_profile
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


