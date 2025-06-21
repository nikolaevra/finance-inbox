"""Authentication API endpoints."""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr
from typing import Optional
from services.auth_service import auth_service, get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Pydantic models for request/response
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_at: int
    user: dict

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Login with email and password"""
    try:
        result = auth_service.login_with_email_password(
            email=request.email,
            password=request.password
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login endpoint error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during login"
        )

@router.post("/refresh")
async def refresh_token(request: RefreshTokenRequest):
    """Refresh access token using refresh token"""
    try:
        result = auth_service.refresh_token(request.refresh_token)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh endpoint error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during token refresh"
        )

@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """Logout current user"""
    try:
        # Note: In a real implementation, you might want to pass the actual token
        # For now, we'll just use the user info to log them out
        result = auth_service.logout(token="") # This could be improved
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Logout endpoint error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during logout"
        )

@router.get("/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information including profile"""
    try:
        # Get user profile from users table
        user_profile = auth_service.get_user_profile(current_user["user_id"])
        
        return {
            "auth": {
                "user_id": current_user["user_id"],
                "email": current_user["email"],
                "role": current_user["role"]
            },
            "profile": user_profile,
            "has_profile": user_profile is not None
        }
    except Exception as e:
        logger.error(f"Error getting user info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving user information"
        )

@router.get("/profile")
async def get_user_profile(current_user: dict = Depends(get_current_user)):
    """Get user profile details"""
    try:
        user_profile = auth_service.get_user_profile(current_user["user_id"])
        
        if user_profile:
            return user_profile
        else:
            # If no profile exists, it means the database trigger might have failed
            # This is unusual but we'll return a helpful message
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found. This may indicate a database trigger issue."
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving user profile"
        )

@router.get("/health")
async def auth_health():
    """Health check for auth service"""
    return {"status": "healthy", "service": "authentication"} 