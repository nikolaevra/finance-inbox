"""Debug API endpoints for troubleshooting authentication"""

from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Optional
import jwt
import os
from services.auth_service import auth_service
import json

router = APIRouter(prefix="/debug", tags=["Debug"])

@router.get("/jwt-info")
def debug_jwt_info(authorization: Optional[str] = Header(None)):
    """Debug endpoint to analyze JWT tokens"""
    
    if not authorization or not authorization.startswith("Bearer "):
        return {"error": "No Bearer token provided"}
    
    token = authorization.replace("Bearer ", "")
    
    try:
        # Decode without verification to see payload
        unverified = jwt.decode(token, options={"verify_signature": False})
        
        # Try to verify with current secret
        jwt_secret = os.getenv("SUPABASE_JWT_SECRET")
        verification_result = None
        
        if jwt_secret:
            try:
                verified = jwt.decode(
                    token, 
                    jwt_secret, 
                    algorithms=["HS256"],
                    audience="authenticated"
                )
                verification_result = {
                    "status": "success",
                    "user_id": verified.get("sub"),
                    "email": verified.get("email")
                }
            except jwt.ExpiredSignatureError:
                verification_result = {"status": "expired", "error": "Token has expired"}
            except jwt.InvalidAudienceError:
                verification_result = {"status": "invalid_audience", "error": f"Invalid audience: {unverified.get('aud')}"}
            except jwt.InvalidSignatureError:
                verification_result = {"status": "invalid_signature", "error": "JWT signature verification failed"}
            except Exception as e:
                verification_result = {"status": "error", "error": str(e)}
        
        return {
            "token_preview": token[:50] + "...",
            "payload": unverified,
            "verification": verification_result,
            "jwt_secret_configured": bool(jwt_secret),
            "jwt_secret_length": len(jwt_secret) if jwt_secret else 0
        }
        
    except Exception as e:
        return {"error": f"Failed to decode token: {str(e)}"}

@router.get("/env-check")
def debug_env_check():
    """Check environment configuration"""
    
    return {
        "supabase_url": os.getenv("SUPABASE_URL"),
        "supabase_key_exists": bool(os.getenv("SUPABASE_KEY")),
        "jwt_secret_exists": bool(os.getenv("SUPABASE_JWT_SECRET")),
        "jwt_secret_length": len(os.getenv("SUPABASE_JWT_SECRET", "")),
        "jwt_secret_preview": os.getenv("SUPABASE_JWT_SECRET", "")[:20] + "..." if os.getenv("SUPABASE_JWT_SECRET") else None
    }

@router.get("/user-profile")
def debug_user_profile(authorization: Optional[str] = Header(None)):
    """Check if user profile exists in database"""
    
    if not authorization or not authorization.startswith("Bearer "):
        return {"error": "No Bearer token provided"}
    
    token = authorization.replace("Bearer ", "")
    
    try:
        # Verify token first
        user_data = auth_service.verify_token(token)
        if not user_data:
            return {"error": "Invalid token"}
        
        # Check if user profile exists
        user_profile = auth_service.get_user_profile(user_data["user_id"])
        
        return {
            "supabase_user_id": user_data["user_id"],
            "email": user_data["email"],
            "profile_exists": bool(user_profile),
            "profile_data": user_profile if user_profile else None
        }
        
    except Exception as e:
        return {"error": f"Failed to check user profile: {str(e)}"} 