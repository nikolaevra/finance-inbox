"""Slack API endpoints that demonstrate automatic token management."""

from fastapi import APIRouter, Depends, HTTPException, status
from services.auth_service import get_current_user_profile
from services.token_manager import token_manager
from models import ConnectionProvider
import logging
import requests

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/slack-api", tags=["Slack API"])

@router.get("/user-info")
def get_slack_user_info(current_user_profile: dict = Depends(get_current_user_profile)):
    """
    Get Slack user information - demonstrates automatic token refresh.
    This endpoint automatically manages Slack tokens before making API calls.
    """
    try:
        user_id = current_user_profile["id"]
        
        # Get valid token (automatically refreshes if needed)
        access_token = token_manager.get_valid_token(user_id, ConnectionProvider.SLACK)
        
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No valid Slack token available. Please reconnect your Slack account."
            )
        
        # Make API call to Slack
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get("https://slack.com/api/auth.test", headers=headers)
        response.raise_for_status()
        
        slack_data = response.json()
        
        if not slack_data.get("ok"):
            logger.error(f"Slack API error: {slack_data.get('error')}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Slack API error: {slack_data.get('error')}"
            )
        
        return {
            "user_id": slack_data.get("user_id"),
            "user": slack_data.get("user"),
            "team_id": slack_data.get("team_id"),
            "team": slack_data.get("team"),
            "url": slack_data.get("url")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Slack user info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get Slack user information"
        )

@router.get("/channels")
def get_slack_channels(current_user_profile: dict = Depends(get_current_user_profile)):
    """
    Get Slack channels - demonstrates automatic token refresh.
    This endpoint automatically manages Slack tokens before making API calls.
    """
    try:
        user_id = current_user_profile["id"]
        
        # Get valid token (automatically refreshes if needed)
        access_token = token_manager.get_valid_token(user_id, ConnectionProvider.SLACK)
        
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No valid Slack token available. Please reconnect your Slack account."
            )
        
        # Make API call to Slack to get channels
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get("https://slack.com/api/conversations.list", headers=headers)
        response.raise_for_status()
        
        slack_data = response.json()
        
        if not slack_data.get("ok"):
            logger.error(f"Slack API error: {slack_data.get('error')}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Slack API error: {slack_data.get('error')}"
            )
        
        channels = slack_data.get("channels", [])
        
        # Format channel data
        formatted_channels = []
        for channel in channels:
            formatted_channels.append({
                "id": channel.get("id"),
                "name": channel.get("name"),
                "is_channel": channel.get("is_channel"),
                "is_private": channel.get("is_private"),
                "is_member": channel.get("is_member"),
                "num_members": channel.get("num_members"),
                "purpose": channel.get("purpose", {}).get("value", ""),
                "topic": channel.get("topic", {}).get("value", "")
            })
        
        return {
            "channels": formatted_channels,
            "count": len(formatted_channels)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Slack channels: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get Slack channels"
        )

@router.get("/test-connection")
def test_slack_connection(current_user_profile: dict = Depends(get_current_user_profile)):
    """
    Test Slack connection status - demonstrates automatic token validation.
    """
    try:
        user_id = current_user_profile["id"]
        
        # Test token validity (handles refresh automatically)
        is_valid = token_manager.test_token_validity(user_id, ConnectionProvider.SLACK)
        
        return {
            "connected": is_valid,
            "provider": "slack",
            "message": "Connection is working" if is_valid else "Connection failed or needs refresh"
        }
        
    except Exception as e:
        logger.error(f"Error testing Slack connection: {str(e)}")
        return {
            "connected": False,
            "provider": "slack",
            "message": f"Connection test failed: {str(e)}"
        } 