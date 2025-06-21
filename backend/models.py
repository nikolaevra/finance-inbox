from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel

class User(BaseModel):
    id: Optional[UUID] = None
    clerk_user_id: str
    email: str
    created_at: Optional[datetime] = None
    business_id: Optional[UUID] = None

class Business(BaseModel):
    id: Optional[UUID] = None
    name: str
    created_at: Optional[datetime] = None

class OAuthToken(BaseModel):
    id: Optional[UUID] = None
    user_id: UUID
    provider: str = "google"
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "Bearer"
    expires_at: datetime
    scope: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class Email(BaseModel):
    id: Optional[UUID] = None
    user_id: UUID
    gmail_id: str
    thread_id: Optional[str] = None
    subject: Optional[str] = None
    from_email: Optional[str] = None
    to_email: Optional[str] = None
    cc_email: Optional[str] = None
    bcc_email: Optional[str] = None
    reply_to: Optional[str] = None
    date_sent: Optional[datetime] = None
    snippet: Optional[str] = None
    body_text: Optional[str] = None
    body_html: Optional[str] = None
    labels: Optional[List[str]] = None
    has_attachments: bool = False
    size_estimate: Optional[int] = None
    is_processed: bool = False
    processed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class EmailAttachment(BaseModel):
    id: Optional[UUID] = None
    email_id: UUID
    filename: Optional[str] = None
    mime_type: Optional[str] = None
    size_bytes: Optional[int] = None
    attachment_id: str  # Gmail attachment ID
    file_path: Optional[str] = None
    is_downloaded: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
