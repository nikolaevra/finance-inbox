"""Authentication service using Supabase Auth."""

import os
import jwt
from typing import Optional, Dict, Any
from datetime import datetime
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from database import get_supabase
from models import UserAuthData
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer token scheme
security = HTTPBearer()

class AuthService:
    def __init__(self):
        self.supabase = get_supabase()
        self.jwt_secret = os.getenv("SUPABASE_JWT_SECRET")
        if not self.jwt_secret:
            raise ValueError("SUPABASE_JWT_SECRET must be set in environment variables")
        self.user_auth_data: Optional[UserAuthData] = None
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return user data"""
        try:
            # Decode the JWT token using Supabase JWT secret
            payload = jwt.decode(
                token, 
                self.jwt_secret, 
                algorithms=["HS256"],
                audience="authenticated"
            )
            
            user_id = payload.get("sub")
            if not user_id:
                return None
                
            return {
                "user_id": user_id,
                "email": payload.get("email"),
                "role": payload.get("role", "authenticated"),
                "exp": payload.get("exp")
            }
        except jwt.ExpiredSignatureError:
            logger.info("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.info(f"Invalid token: {e}")
            return None
    
    def get_user_auth_data(self) -> UserAuthData:
        """Get the stored user auth data"""
        if not self.user_auth_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No user auth data found"
            )
        
        return self.user_auth_data
    
    def login_with_email_password(self, email: str, password: str) -> Dict[str, Any]:
        """Login user with email and password using Supabase Auth"""
        try:
            response = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if response.user and response.session:
                logger.info(f"✅ User logged in successfully: {email}")
                self.user_auth_data = UserAuthData(
                    access_token=response.session.access_token,
                    refresh_token=response.session.refresh_token,
                    token_type="bearer",
                    expires_at=response.session.expires_at if response.session.expires_at is not None else 0,
                    user={
                        "id": response.user.id,
                        "email": response.user.email,
                        "email_confirmed_at": response.user.email_confirmed_at,
                        "last_sign_in_at": response.user.last_sign_in_at
                    }
                )
                return self.user_auth_data.to_dict()
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )
                
        except Exception as e:
            logger.error(f"❌ Login failed for {email}: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Login failed. Please check your credentials."
            )
    
    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile from users table"""
        try:
            # The user_id from the token 'sub' claim corresponds to 'supabase_user_id' in our public 'users' table
            result = self.supabase.table("users").select("*").eq("supabase_user_id", user_id).single().execute()
            
            if result.data:
                return result.data
            else:
                logger.warning(f"No user profile found for user_id: {user_id}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error fetching user profile for {user_id}: {e}")
            return None
    
    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token using refresh token"""
        try:
            response = self.supabase.auth.refresh_session(refresh_token)
            
            if response.session:
                # Update the stored auth data with refreshed tokens
                if self.user_auth_data:
                    self.user_auth_data.access_token = response.session.access_token
                    self.user_auth_data.refresh_token = response.session.refresh_token
                    self.user_auth_data.expires_at = response.session.expires_at if response.session.expires_at is not None else 0
                    return self.user_auth_data.to_dict()
                else:
                    # If no stored auth data, create a minimal response
                    return {
                        "access_token": response.session.access_token,
                        "refresh_token": response.session.refresh_token,
                        "expires_at": response.session.expires_at,
                        "token_type": "bearer"
                    }
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Failed to refresh token"
                )
                
        except Exception as e:
            logger.error(f"❌ Token refresh failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to refresh token"
            )
    
    def logout(self, token: str) -> Dict[str, str]:
        """Logout user and invalidate session"""
        try:
            # Sign out the user
            self.supabase.auth.sign_out()
            
            # Clear stored auth data
            self.user_auth_data = None
            
            logger.info("✅ User logged out successfully")
            return {"message": "Logged out successfully"}
            
        except Exception as e:
            logger.error(f"❌ Logout failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Logout failed"
            )

# Initialize auth service
auth_service = AuthService()

async def get_current_user_auth_data(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Dependency to extract user auth data from JWT token (Supabase client-side auth)"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_data = auth_service.verify_token(credentials.credentials)
    
    if not user_data:
        # Token is invalid/expired - let frontend handle refresh via Supabase client
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired. Please refresh your session.",
            headers={
                "WWW-Authenticate": "Bearer",
                "X-Auth-Action": "refresh-required"  # Tell frontend to refresh token
            },
        )
    
    return user_data

# Dependency to get current user profile from JWT token with automatic refresh
async def get_current_user_profile(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    Dependency to extract user profile from JWT token.
    This is the primary method for protecting routes and getting the current user.
    """
    # First, verify the token and get the basic user data (including user_id from 'sub' claim)
    user_auth_data = await get_current_user_auth_data(credentials)
    user_id = user_auth_data.get("user_id")

    if not user_id:
        # This case should ideally be caught by get_current_user_auth_data, but as a safeguard:
        logger.error("Critical: User auth data is missing user_id after token verification.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not determine user identity from token."
        )

    # Now, fetch the detailed user profile from the database
    user_profile = auth_service.get_user_profile(user_id)
    
    if not user_profile:
        logger.error(f"No user profile found in the database for a valid user token (user_id: {user_id})")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found. The user may have been deleted."
        )
    
    # Ensure we have the user_id from the database (the actual primary key 'id')
    # This is what other tables reference, not the supabase_user_id
    if 'id' in user_profile:
        user_profile['user_id'] = user_profile['id']  # Use the database primary key
    else:
        # Fallback: if somehow 'id' is missing, use the supabase_user_id
        logger.warning(f"User profile missing 'id' field for user {user_id}")
        user_profile['user_id'] = user_id
    
    # Also include the supabase_user_id for reference
    user_profile['supabase_user_id'] = user_id
    
    return user_profile

