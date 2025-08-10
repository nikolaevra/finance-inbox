"""Token manager service for automatic OAuth token refresh."""

import logging
from typing import Optional, Dict, Any
from uuid import UUID
from services.google_service import GoogleService
from services.slack_service import SlackService
from models import ConnectionProvider

logger = logging.getLogger(__name__)

class TokenManager:
    """Manages automatic token refresh for OAuth providers."""
    
    @staticmethod
    def get_valid_token(user_id: str, provider: ConnectionProvider) -> Optional[str]:
        """
        Get a valid access token for the specified provider.
        Automatically refreshes the token if it's expired.
        
        Args:
            user_id: Internal user ID
            provider: The OAuth provider (GMAIL or SLACK)
            
        Returns:
            Valid access token or None if unavailable/expired
        """
        try:
            logger.info(f"🔑 Getting valid token for {provider.value} for user {user_id}")
            
            if provider == ConnectionProvider.GMAIL:
                google_service = GoogleService(internal_user_id=user_id)
                
                # Try to refresh the token first
                if google_service.refresh_access_token():
                    # Get token from database after refresh
                    tokens = google_service._get_tokens_from_db()
                    if tokens:
                        return tokens.access_token
                    else:
                        logger.warning(f"⚠️ No tokens found after refresh for user {user_id}")
                        return None
                else:
                    logger.warning(f"⚠️ Failed to refresh Gmail token for user {user_id}")
                    return None
                    
            elif provider == ConnectionProvider.SLACK:
                slack_service = SlackService(internal_user_id=user_id)
                
                # For Slack, get the valid token (refresh is handled internally)
                return slack_service.get_valid_token()
                
            else:
                logger.error(f"❌ Unsupported provider: {provider}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error getting valid token for {provider.value}: {str(e)}")
            return None
    
    @staticmethod
    def test_token_validity(user_id: str, provider: ConnectionProvider) -> bool:
        """
        Test if the user's token for the provider is valid.
        
        Args:
            user_id: Internal user ID
            provider: The OAuth provider
            
        Returns:
            True if token is valid, False otherwise
        """
        try:
            if provider == ConnectionProvider.GMAIL:
                google_service = GoogleService(internal_user_id=user_id)
                return google_service.test_connection()
                
            elif provider == ConnectionProvider.SLACK:
                slack_service = SlackService(internal_user_id=user_id)
                return slack_service.test_connection()
                
            else:
                logger.error(f"❌ Unsupported provider: {provider}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error testing token validity for {provider.value}: {str(e)}")
            return False
    
    @staticmethod
    def refresh_all_tokens(user_id: str) -> Dict[str, bool]:
        """
        Refresh all tokens for a user across all providers.
        
        Args:
            user_id: Internal user ID
            
        Returns:
            Dictionary with provider names as keys and success status as values
        """
        results = {}
        
        try:
            # Refresh Gmail token
            try:
                google_service = GoogleService(internal_user_id=user_id)
                results['gmail'] = google_service.refresh_access_token()
            except Exception as e:
                logger.error(f"❌ Error refreshing Gmail token: {str(e)}")
                results['gmail'] = False
            
            # Check Slack token (Slack tokens typically don't need refresh)
            try:
                slack_service = SlackService(internal_user_id=user_id)
                results['slack'] = slack_service.refresh_access_token()
            except Exception as e:
                logger.error(f"❌ Error checking Slack token: {str(e)}")
                results['slack'] = False
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Error refreshing tokens for user {user_id}: {str(e)}")
            return {'gmail': False, 'slack': False}

# Create singleton instance
token_manager = TokenManager() 