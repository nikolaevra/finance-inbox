"""Inbox API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from services.google_service import GoogleService
from services.auth_service import get_current_user_profile
import logging
from typing import Optional, List

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/inbox", tags=["Inbox"])

class EmailReplyRequest(BaseModel):
    """Request model for email replies"""
    reply_body: str
    reply_subject: Optional[str] = None
    to: Optional[List[str]] = None  # Override reply recipients
    cc: Optional[List[str]] = None  # Add CC recipients
    bcc: Optional[List[str]] = None  # Add BCC recipients



@router.get("/")
def get_inbox(limit: int = 50, offset: int = 0, current_user_profile: dict = Depends(get_current_user_profile)):
    """Get user's inbox organized by email threads"""
    google_service = GoogleService(internal_user_id=current_user_profile["user_id"])
    threads = google_service.get_inbox_threads(limit=limit, offset=offset)
    
    # Calculate total email count across all threads
    total_emails = sum(thread.get('email_count', 0) for thread in threads)
    
    return {
        "threads": threads,
        "thread_count": len(threads),
        "total_emails": total_emails,
        "limit": limit,
        "offset": offset,
        "source": "database"
    }

@router.get("/emails")
def get_emails(limit: int = 50, offset: int = 0, current_user_profile: dict = Depends(get_current_user_profile)):
    """Get user's emails as individual items (non-threaded view)"""
    google_service = GoogleService(internal_user_id=current_user_profile["user_id"])
    emails = google_service.get_inbox_emails(limit=limit, offset=offset)
    return {
        "emails": emails,
        "count": len(emails),
        "limit": limit,
        "offset": offset,
        "source": "database"
    }

@router.post("/emails/sync")
def sync_emails(max_results: int = 50, current_user_profile: dict = Depends(get_current_user_profile)):
    """Fetch emails from Gmail and store them in database"""
    google_service = GoogleService(internal_user_id=current_user_profile["user_id"])
    emails = google_service.fetch_gmail_emails(max_results=max_results, only_new=True)
    return {
        "message": f"Successfully synced {len(emails)} emails",
        "emails_synced": len(emails),
        "source": "gmail_api"
    }

@router.put("/email/{email_id}/read")
def mark_email_as_read(email_id: str, current_user_profile: dict = Depends(get_current_user_profile)):
    """Mark an email as read"""
    google_service = GoogleService(internal_user_id=current_user_profile["user_id"])
    success = google_service.mark_email_as_read(email_id)
    if success:
        return {"message": "Email marked as read", "email_id": email_id}
    else:
        raise HTTPException(status_code=404, detail="Email not found")

@router.put("/thread/{thread_id}/read")
def mark_thread_as_read(thread_id: str, current_user_profile: dict = Depends(get_current_user_profile)):
    """Mark all emails in a thread as read"""
    google_service = GoogleService(internal_user_id=current_user_profile["user_id"])
    count = google_service.mark_thread_as_read(thread_id)
    return {"message": f"Marked {count} emails as read in thread", "thread_id": thread_id}



@router.get("/email/{email_id}")
def get_single_email(email_id: str, current_user_profile: dict = Depends(get_current_user_profile)):
    """Get detailed information for a single email from database"""
    google_service = GoogleService(internal_user_id=current_user_profile["user_id"])
    email = google_service.get_single_email_from_db(email_id)
    
    if not email:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Email with ID {email_id} not found"
        )
    
    return email

@router.get("/thread/{thread_id}")
def get_thread(thread_id: str, current_user_profile: dict = Depends(get_current_user_profile)):
    """Get a specific email thread with all emails in conversation"""
    google_service = GoogleService(internal_user_id=current_user_profile["user_id"])
    thread = google_service.get_thread_by_id(thread_id)
    
    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Thread {thread_id} not found"
        )
    
    return thread

@router.post("/email/{email_id}/reply")
def reply_to_email(email_id: str, reply_request: EmailReplyRequest, current_user_profile: dict = Depends(get_current_user_profile)):
    """Reply to an email using Gmail API with customizable recipients"""
    logger.info(f"📤 Processing reply request for email {email_id}")
    
    google_service = GoogleService(internal_user_id=current_user_profile["user_id"])
    
    # Send the reply using GoogleService with all recipient options
    result = google_service.send_email_reply(
        original_email_id=email_id,
        reply_body=reply_request.reply_body,
        reply_subject=reply_request.reply_subject or "",
        to=reply_request.to,
        cc=reply_request.cc,
        bcc=reply_request.bcc
    )
    
    # Check if the reply was sent successfully
    if result.get("error"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    logger.info(f"✅ Reply sent successfully for email {email_id}")
    
    return {
        "message": f"Successfully sent reply for email {email_id}",
        "email_id": email_id,
    }


