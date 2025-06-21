from datetime import datetime
from typing import Optional
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
