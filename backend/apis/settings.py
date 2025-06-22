"""Settings API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from services.google_service import GoogleService
from services.auth_service import get_current_user_profile
from services.connections_service import connections_service
from models import ConnectionProvider
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/settings", tags=["Settings"])

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
