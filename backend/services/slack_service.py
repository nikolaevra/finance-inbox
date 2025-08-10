import os
import logging
import requests
from datetime import datetime, timedelta, timezone
from typing import Optional, Union
from uuid import UUID
from dotenv import load_dotenv
from database import get_supabase
from models import OAuthToken, ConnectionProvider, ConnectionStatus
from services.connections_service import connections_service

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

class SlackService:
    def __init__(self, internal_user_id: Optional[Union[str, UUID]] = None):
        self.client_id = os.environ["SLACK_CLIENT_ID"]
        self.client_secret = os.environ["SLACK_CLIENT_SECRET"]
        self.redirect_uri = os.environ["SLACK_REDIRECT_URI"]
        self.internal_user_id = str(internal_user_id) if internal_user_id else None
        self.scopes = [
            "channels:read",
            "channels:history",
            "users:read",
            "team:read"
        ]
        self.supabase = get_supabase()
        
        # Log initialization
        if self.internal_user_id:
            logger.info(f"🔧 SlackService initialized for internal_user_id: {self.internal_user_id}")
        else:
            logger.info("🔧 SlackService initialized without user context")

    def _ensure_utc(self, dt: datetime) -> datetime:
        """Ensure a datetime is in UTC timezone"""
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    def _get_tokens_from_db(self) -> Optional[OAuthToken]:
        """Retrieve tokens from database through connections table"""
        logger.info(f"🔍 Retrieving Slack tokens for internal_user_id: {self.internal_user_id}")
        
        if not self.internal_user_id:
            logger.warning("❌ No internal_user_id available, cannot retrieve tokens")
            return None
            
        try:
            # First, get the Slack connection for this user
            logger.debug(f"📊 Looking up Slack connection for user_id: {self.internal_user_id}")
            connection_result = self.supabase.table("connections").select("oauth_token_id").eq("user_id", str(self.internal_user_id)).eq("connection_provider", "slack").single().execute()
            
            if not connection_result.data or not connection_result.data.get('oauth_token_id'):
                logger.info(f"🔍 No Slack connection or oauth_token_id found for user {self.internal_user_id}")
                return None
            
            oauth_token_id = connection_result.data['oauth_token_id']
            logger.debug(f"📊 Found oauth_token_id: {oauth_token_id}, retrieving token details")
            
            # Now get the OAuth token using the ID from connection
            token_result = self.supabase.table("oauth_tokens").select("*").eq("id", oauth_token_id).eq("provider", "slack").single().execute()
            
            if token_result.data:
                token = OAuthToken(**token_result.data)
                logger.info(f"✅ Found Slack tokens for user {self.internal_user_id}, expires at: {token.expires_at}")
                return token
            else:
                logger.info(f"🔍 No OAuth token found with ID {oauth_token_id}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error retrieving Slack tokens for user {self.internal_user_id}: {str(e)}")
            return None

    def _save_tokens_to_db(
        self, 
        access_token: str,
        refresh_token: str = "",
        expires_at: datetime = None,
        scope: str = "",
        team_info: dict = None
    ) -> bool:
        """Save Slack OAuth tokens to database"""
        try:
            if not self.internal_user_id:
                logger.error("❌ Cannot save tokens: no user ID provided")
                return False

            # Default expiry to 12 hours if not provided (Slack tokens don't typically expire)
            if expires_at is None:
                expires_at = datetime.now(timezone.utc) + timedelta(hours=12)
            
            expires_at = self._ensure_utc(expires_at)
            
            token_data = {
                "provider": "slack",
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "Bearer",
                "expires_at": expires_at.isoformat(),
                "scope": scope,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            logger.info(f"💾 Saving Slack tokens to database for user {self.internal_user_id}")
            
            # Check if we have an existing connection with oauth_token_id
            existing_token = self._get_tokens_from_db()
            if existing_token:
                logger.info(f"🔄 Updating existing tokens for user {self.internal_user_id}")
                result = self.supabase.table("oauth_tokens").update(token_data).eq("id", existing_token.id).execute()
                oauth_token_id = existing_token.id
            else:
                logger.info(f"➕ Inserting new tokens for user {self.internal_user_id}")
                result = self.supabase.table("oauth_tokens").insert(token_data).execute()
                if result.data and len(result.data) > 0:
                    oauth_token_id = result.data[0]['id']
                else:
                    logger.error("❌ Failed to get oauth_token_id from insert result")
                    return False
            
            # Update the connection with the oauth_token_id
            if oauth_token_id:
                logger.debug(f"🔗 Updating connection with oauth_token_id: {oauth_token_id}")
                
                # First, try to update existing connection
                connection_update = self.supabase.table("connections").update({
                    "oauth_token_id": oauth_token_id,
                    "status": ConnectionStatus.CONNECTED.value,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }).eq("user_id", self.internal_user_id).eq("connection_provider", "slack").execute()
                
                # Check if update affected any rows
                if connection_update.data and len(connection_update.data) > 0:
                    logger.info("✅ Successfully updated existing connection")
                    return True
                else:
                    # No existing connection found, create a new one
                    logger.info("🔗 No existing connection found, creating new one")
                    
                    metadata = {
                        "scopes": self.scopes,
                        "connected_at": datetime.now(timezone.utc).isoformat()
                    }
                    
                    if team_info:
                        metadata.update({
                            "team_id": team_info.get("id"),
                            "team_name": team_info.get("name"),
                            "team_domain": team_info.get("domain")
                        })
                    
                    connection_data = {
                        "user_id": self.internal_user_id,
                        "connection_provider": "slack",
                        "status": ConnectionStatus.CONNECTED.value,
                        "oauth_token_id": oauth_token_id,
                        "metadata": metadata,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }
                    
                    connection_create = self.supabase.table("connections").insert(connection_data).execute()
                    
                    if connection_create.data:
                        logger.info("✅ Successfully created new connection with tokens")
                        return True
                    else:
                        logger.error("❌ Failed to create new connection")
                        return False
            else:
                logger.error("❌ No oauth_token_id available to update connection")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error saving Slack tokens to database: {str(e)}")
            return False

    def _create_slack_connection(self, oauth_token_id: str = None, team_info: dict = None) -> bool:
        """Create Slack connection record after successful OAuth"""
        try:
            logger.info(f"🔗 Creating Slack connection record for user {self.internal_user_id}")
            
            metadata = {
                "scopes": self.scopes,
                "connected_at": datetime.now(timezone.utc).isoformat()
            }
            
            if team_info:
                metadata.update({
                    "team_id": team_info.get("id"),
                    "team_name": team_info.get("name"),
                    "team_domain": team_info.get("domain")
                })
            
            # Create/update connection record (oauth_token_id will be set by _save_tokens_to_db)
            success = connections_service.create_or_update_connection(
                user_id=self.internal_user_id,
                provider=ConnectionProvider.SLACK,
                status=ConnectionStatus.CONNECTED,
                oauth_token_id=None,  # This will be updated by _save_tokens_to_db
                metadata=metadata
            )
            
            if success:
                logger.info("✅ Successfully created Slack connection record")
                return True
            else:
                logger.error("❌ Failed to create Slack connection record")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error creating Slack connection record: {str(e)}")
            return False

    def get_authorization_url(self, state: str = None) -> str:
        """Generate Slack OAuth authorization URL"""
        if not self.client_id:
            raise ValueError("SLACK_CLIENT_ID environment variable not set")
        
        if not self.redirect_uri:
            raise ValueError("SLACK_REDIRECT_URI environment variable not set")
        
        logger.info(f"🌐 Generating Slack authorization URL for user {self.internal_user_id}")
        
        # Build authorization URL
        scope_string = ",".join(self.scopes)
        
        params = {
            "client_id": self.client_id,
            "scope": scope_string,
            "redirect_uri": self.redirect_uri,
            "response_type": "code"
        }
        
        if state:
            params["state"] = state
        
        # Build URL manually to ensure proper encoding
        base_url = "https://slack.com/oauth/v2/authorize"
        param_string = "&".join([f"{k}={requests.utils.quote(str(v))}" for k, v in params.items()])
        authorization_url = f"{base_url}?{param_string}"
        
        logger.info("✅ Successfully generated Slack authorization URL")
        return authorization_url

    def handle_oauth_callback(self, code: str) -> dict:
        """Handle Slack OAuth callback and exchange code for tokens"""
        try:
            if not self.client_id or not self.client_secret:
                raise ValueError("Slack OAuth credentials not configured")
            
            logger.info("🌐 Exchanging authorization code for Slack tokens...")
            
            # Exchange code for access token
            token_url = "https://slack.com/api/oauth.v2.access"
            
            payload = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "code": code,
                "redirect_uri": self.redirect_uri
            }
            
            response = requests.post(token_url, data=payload)
            response.raise_for_status()
            
            token_data = response.json()
            
            if not token_data.get("ok"):
                error = token_data.get("error", "Unknown error")
                logger.error(f"❌ Slack OAuth error: {error}")
                return {"error": f"Slack OAuth failed: {error}"}
            
            access_token = token_data.get("access_token")
            if not access_token:
                logger.error("❌ No access token received from Slack")
                return {"error": "No access token received"}
            
            logger.info("✅ Successfully received tokens from Slack")
            
            # Get team information
            team_info = token_data.get("team", {})
            scope_string = ",".join(self.scopes)
            
            # Slack tokens typically don't expire, but we'll set a far future date
            expires_at = datetime.now(timezone.utc) + timedelta(days=365)
            
            logger.info(f"💾 Attempting to save tokens for user {self.internal_user_id}")
            
            # Save tokens to database
            if self._save_tokens_to_db(
                access_token=access_token,
                refresh_token="",  # Slack doesn't use refresh tokens in OAuth v2
                expires_at=expires_at,
                scope=scope_string,
                team_info=team_info
            ):
                logger.info(f"✅ Slack OAuth flow completed successfully for user {self.internal_user_id}")
                
                return {"message": "Slack authentication complete. Tokens saved to database."}
            else:
                logger.error(f"❌ Failed to save tokens to database for user {self.internal_user_id}")
                return {"error": "Failed to save tokens to database"}
                
        except Exception as e:
            logger.error(f"❌ Error in Slack OAuth callback: {str(e)}")
            return {"error": f"OAuth callback failed: {str(e)}"}

    def refresh_access_token(self) -> bool:
        """
        Refresh Slack access token if needed.
        Note: Slack OAuth v2 tokens typically don't expire, but this method
        is here for consistency with other OAuth providers.
        """
        try:
            logger.info(f"🔄 Checking Slack token status for user {self.internal_user_id}")
            
            # Get current token from database
            token_record = self._get_tokens_from_db()
            if not token_record:
                logger.warning("⚠️ No Slack token found for user")
                return False
            
            expires_at = token_record.expires_at
            if isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
            
            # Check if token is still valid (with 1 hour buffer)
            if expires_at > datetime.now(timezone.utc) + timedelta(hours=1):
                logger.info("✅ Slack token is still valid")
                return True
            
            logger.info("🔄 Slack token needs refresh (though this is unusual for Slack)")
            
            # For Slack, we would typically need to re-authenticate
            # as Slack OAuth v2 tokens don't have a refresh mechanism
            logger.warning("⚠️ Slack token expired - user needs to re-authenticate")
            
            # Update connection status to require refresh
            connections_service.create_or_update_connection(
                user_id=self.internal_user_id,
                provider=ConnectionProvider.SLACK,
                status=ConnectionStatus.REFRESH_REQUIRED
            )
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Error refreshing Slack token: {str(e)}")
            return False

    def get_valid_token(self) -> Optional[str]:
        """Get a valid access token, refreshing if necessary"""
        try:
            if self.refresh_access_token():
                # Get token from database using the connections table
                tokens = self._get_tokens_from_db()
                if tokens:
                    return tokens.access_token
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting valid Slack token: {str(e)}")
            return None

    def test_connection(self) -> bool:
        """Test if the Slack connection is working"""
        try:
            token = self.get_valid_token()
            if not token:
                return False
            
            # Test the connection by calling Slack's auth.test endpoint
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get("https://slack.com/api/auth.test", headers=headers)
            response.raise_for_status()
            
            result = response.json()
            return result.get("ok", False)
            
        except Exception as e:
            logger.error(f"❌ Error testing Slack connection: {str(e)}")
            return False 