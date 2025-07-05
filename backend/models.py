from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel
from dataclasses import dataclass
from enum import Enum

class ConnectionStatus(str, Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    REFRESH_REQUIRED = "refresh_required"

class ConnectionProvider(str, Enum):
    GMAIL = "gmail"

@dataclass
class UserAuthData:
    """Structured object representing user authentication data"""
    access_token: str
    refresh_token: str
    token_type: str
    expires_at: int
    user: dict
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses"""
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "token_type": self.token_type,
            "expires_at": self.expires_at,
            "user": self.user
        }

@dataclass
class EmailDetails:
    """Structured object representing email details from Gmail API"""
    id: str
    thread_id: Optional[str]
    subject: str
    from_email: str
    to_email: str
    date: str
    snippet: str
    body: dict  # Contains 'text' and 'html' keys
    labels: List[str]
    has_attachments: bool
    size_estimate: int
    cc_email: Optional[str] = None
    bcc_email: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses and database storage"""
        return {
            "id": self.id,
            "thread_id": self.thread_id,
            "subject": self.subject,
            "from": self.from_email,
            "to": self.to_email,
            "date": self.date,
            "snippet": self.snippet,
            "body": self.body,
            "labels": self.labels,
            "has_attachments": self.has_attachments,
            "size_estimate": self.size_estimate,
            "cc_email": self.cc_email,
            "bcc_email": self.bcc_email
        }

class User(BaseModel):
    id: Optional[UUID] = None
    supabase_user_id: str  # This connects to auth.users.id in Supabase
    email: str
    created_at: Optional[datetime] = None
    business_id: Optional[UUID] = None
    # Additional profile fields
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    last_sign_in_at: Optional[datetime] = None

class Business(BaseModel):
    id: Optional[UUID] = None
    name: str
    created_at: Optional[datetime] = None

class Connection(BaseModel):
    id: Optional[UUID] = None
    user_id: UUID  # References users.id
    connection_provider: ConnectionProvider
    status: ConnectionStatus
    oauth_token_id: Optional[UUID] = None  # References oauth_tokens.id
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_sync_at: Optional[datetime] = None
    metadata: Optional[dict] = None  # Store provider-specific metadata

class OAuthToken(BaseModel):
    id: Optional[UUID] = None
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
