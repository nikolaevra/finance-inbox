import os
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from dotenv import load_dotenv
from database import get_supabase
from models import OAuthToken

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

class GoogleService:
    def __init__(self, user_id: Optional[UUID] = None):
        self.client_id = os.environ["GOOGLE_CLIENT_ID"]
        self.client_secret = os.environ["GOOGLE_CLIENT_SECRET"]
        self.redirect_uri = os.environ["GOOGLE_REDIRECT_URI"]
        self.user_id = user_id  # Will need to be set for database operations
        self.scopes = [
            "https://www.googleapis.com/auth/gmail.readonly",
            "openid",
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile"
        ]
        self.supabase = get_supabase()

    def _ensure_utc(self, dt: datetime) -> datetime:
        """Ensure a datetime is in UTC timezone"""
        if dt.tzinfo is None:
            # Naive datetime, assume it's UTC
            return dt.replace(tzinfo=timezone.utc)
        else:
            # Convert to UTC if it's in a different timezone
            return dt.astimezone(timezone.utc)

    def _get_tokens_from_db(self) -> Optional[OAuthToken]:
        """Retrieve tokens from database for the current user"""
        logger.info(f"🔍 Retrieving tokens for user_id: {self.user_id}")
        
        if not self.user_id:
            logger.warning("❌ No user_id provided, cannot retrieve tokens")
            return None
            
        try:
            logger.debug(f"📊 Querying oauth_tokens table for user_id: {self.user_id}, provider: google")
            result = self.supabase.table("oauth_tokens").select("*").eq("user_id", str(self.user_id)).eq("provider", "google").single().execute()
            
            if result.data:
                token = OAuthToken(**result.data)
                logger.info(f"✅ Found tokens for user {self.user_id}, expires at: {token.expires_at}")
                return token
            else:
                logger.info(f"🔍 No tokens found for user {self.user_id}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error retrieving tokens for user {self.user_id}: {str(e)}")
            return None

    def _save_tokens_to_db(self, access_token: str, refresh_token: str, expires_at: datetime, scope: str) -> bool:
        """Save or update tokens in database"""
        logger.info(f"💾 Saving tokens for user_id: {self.user_id}, expires at: {expires_at}")
        
        if not self.user_id:
            logger.warning("❌ No user_id provided, cannot save tokens")
            return False
            
        try:
            # Ensure expires_at is always stored in UTC
            expires_at_utc = self._ensure_utc(expires_at)
            
            token_data = {
                "user_id": str(self.user_id),
                "provider": "google",
                "access_token": access_token,
                "refresh_token": refresh_token,
                "expires_at": expires_at_utc.isoformat(),
                "scope": scope
            }
            
            logger.debug(f"📅 Storing expiry time in UTC: {expires_at_utc.isoformat()}")
            logger.debug(f"📝 Token data prepared: user_id={self.user_id}, provider=google, expires_at={expires_at_utc.isoformat()}")
            
            # Try to update existing token first
            existing = self._get_tokens_from_db()
            if existing:
                logger.info(f"🔄 Updating existing tokens for user {self.user_id}")
                result = self.supabase.table("oauth_tokens").update(token_data).eq("user_id", str(self.user_id)).eq("provider", "google").execute()
            else:
                logger.info(f"➕ Inserting new tokens for user {self.user_id}")
                result = self.supabase.table("oauth_tokens").insert(token_data).execute()
            
            success = len(result.data) > 0
            if success:
                logger.info(f"✅ Successfully saved tokens for user {self.user_id}")
            else:
                logger.warning(f"⚠️ No data returned when saving tokens for user {self.user_id}")
                
            return success
        except Exception as e:
            logger.error(f"❌ Error saving tokens for user {self.user_id}: {str(e)}")
            return False

    def _delete_tokens_from_db(self) -> bool:
        """Delete tokens from database"""
        if not self.user_id:
            return False
            
        try:
            result = self.supabase.table("oauth_tokens").delete().eq("user_id", str(self.user_id)).eq("provider", "google").execute()
            return True
        except Exception as e:
            print(f"Error deleting tokens: {str(e)}")
            return False

    def get_authorization_url(self) -> str:
        """Generate Google OAuth authorization URL"""
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=self.scopes,
            redirect_uri=self.redirect_uri,
        )
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'  # Force consent screen to get refresh token
        )

        # sample response
        # http://localhost:8000/google-auth/callback?state=GOLiQkZMcRKwNHwbKj54YmTXIHXTxs&code=4/0AVMBsJi28MvE2Bkd1NT-DMD8raESHNbJpsHQ2SacQEuxidtH5XJZiDEtSQaf0aUQjNffQA&scope=email%20profile%20https://www.googleapis.com/auth/gmail.readonly%20https://www.googleapis.com/auth/userinfo.profile%20https://www.googleapis.com/auth/userinfo.email%20openid&authuser=1&prompt=consent

        # Save state in session if you use one
        return authorization_url

    def handle_oauth_callback(self, code: str) -> dict:
        """Handle OAuth callback and store tokens"""
        logger.info(f"🔐 Handling OAuth callback for user {self.user_id}")
        
        if not code:
            logger.warning("❌ No authorization code provided in callback")
            return {"error": "No authorization code provided"}

        logger.debug("🔑 Creating OAuth flow for token exchange")
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=self.scopes,
            redirect_uri=self.redirect_uri,
        )
        
        try:
            logger.info("🌐 Exchanging authorization code for tokens...")
            flow.fetch_token(code=code)
            credentials = flow.credentials
            logger.info("✅ Successfully received tokens from Google")
            
            # Log what tokens we received (for debugging)
            logger.info(f"🔑 Access token received: {'✅' if credentials.token else '❌'}")
            logger.info(f"🔄 Refresh token received: {'✅' if credentials.refresh_token else '❌'}")
            if not credentials.refresh_token:
                logger.warning("⚠️ No refresh token received - user may have already granted consent")
            
            # Calculate expiry time (use UTC for consistency)
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=3600)  # 1 hour from now
            scope_string = " ".join(self.scopes)
            
            logger.info(f"💾 Attempting to save tokens for user {self.user_id}, expires at: {expires_at}")
            
            # Save tokens to database
            if self._save_tokens_to_db(
                access_token=credentials.token,
                refresh_token=credentials.refresh_token or "",  # Handle None refresh token
                expires_at=expires_at,
                scope=scope_string
            ):
                logger.info(f"✅ OAuth flow completed successfully for user {self.user_id}")
                return {"message": "Authentication complete. Tokens saved to database."}
            else:
                logger.error(f"❌ Failed to save tokens to database for user {self.user_id}")
                return {"error": "Failed to save tokens to database"}
                
        except Exception as e:
            logger.error(f"❌ OAuth callback failed for user {self.user_id}: {str(e)}")
            return {"error": f"Authentication failed: {str(e)}"}

    def fetch_gmail_emails(self) -> list:
        """Fetch Gmail emails using stored credentials"""
        logger.info(f"📧 Starting Gmail email fetch for user {self.user_id}")
        
        # Get tokens from database
        tokens = self._get_tokens_from_db()
        if not tokens:
            logger.warning(f"❌ No tokens available for user {self.user_id}, cannot fetch emails")
            return []

        try:
            # Check if token needs refresh
            logger.info("🔄 Checking if token refresh is needed before fetching emails")
            if not self._refresh_token_if_needed():
                logger.error(f"❌ Token refresh failed for user {self.user_id}, cannot fetch emails")
                return []
            
            # Get fresh tokens after potential refresh
            logger.debug("🔍 Getting fresh tokens after refresh check")
            tokens = self._get_tokens_from_db()
            if not tokens:
                logger.error(f"❌ No tokens found after refresh for user {self.user_id}")
                return []

            # Build credentials object
            logger.debug("🔑 Building Google credentials object")
            creds_obj = Credentials(
                tokens.access_token,
                refresh_token=tokens.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.client_id,
                client_secret=self.client_secret,
            )
            
            # Build Gmail service
            logger.debug("🔧 Building Gmail API service")
            service = build('gmail', 'v1', credentials=creds_obj)
            
            # Fetch messages
            logger.info("🌐 Fetching messages from Gmail API (max 10)")
            result = service.users().messages().list(
                userId='me', 
                maxResults=10
            ).execute()
            
            messages = result.get('messages', [])
            logger.info(f"📨 Found {len(messages)} messages")
            
            emails = []
            
            for i, msg in enumerate(messages):
                logger.debug(f"📧 Fetching details for message {i+1}/{len(messages)}: {msg['id']}")
                msg_data = service.users().messages().get(
                    userId='me', 
                    id=msg['id']
                ).execute()
                
                snippet = msg_data.get('snippet')
                emails.append({
                    'id': msg['id'],
                    'snippet': snippet,
                })
            
            logger.info(f"✅ Successfully fetched {len(emails)} emails for user {self.user_id}")
            return emails
            
        except Exception as e:
            logger.error(f"❌ Error fetching emails for user {self.user_id}: {str(e)}")
            return []

    def get_tokens(self) -> dict:
        """Get stored tokens (for debugging/testing)"""
        tokens = self._get_tokens_from_db()
        if not tokens:
            return {}
        return {
            "access_token": tokens.access_token[:20] + "..." if tokens.access_token else None,
            "has_refresh_token": bool(tokens.refresh_token),
            "expires_at": tokens.expires_at.isoformat() if tokens.expires_at else None
        }

    def clear_tokens(self) -> dict:
        """Clear stored tokens"""
        if self._delete_tokens_from_db():
            return {"message": "Tokens cleared from database"}
        else:
            return {"message": "No tokens found or failed to clear"}

    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        tokens = self._get_tokens_from_db()
        return bool(tokens and tokens.access_token)

    def _refresh_token_if_needed(self) -> bool:
        """Refresh access token if it's expired or about to expire"""
        logger.info(f"🔄 Checking if token refresh is needed for user {self.user_id}")
        
        tokens = self._get_tokens_from_db()
        if not tokens:
            logger.warning(f"❌ No tokens found for user {self.user_id}")
            return False
        
        # Check if token is expired or expires in the next 5 minutes
        # Ensure we're using timezone-aware datetime for comparison
        now = datetime.now(timezone.utc)
        
        # Ensure database datetime is in UTC for comparison
        expires_at = self._ensure_utc(tokens.expires_at)
            
        time_until_expiry = expires_at - now
        logger.info(f"⏰ Token expires in {time_until_expiry.total_seconds():.0f} seconds")
        
        # If token is still valid (more than 5 minutes left), no refresh needed
        if now < (expires_at - timedelta(minutes=5)):
            logger.info(f"✅ Token is still valid for user {self.user_id} (expires in {time_until_expiry.total_seconds():.0f} seconds)")
            return True
        
        # Token needs refresh - NOW check if we have a refresh token
        if not tokens.refresh_token:
            logger.error(f"❌ Token expired/expiring but no refresh token available for user {self.user_id}")
            return False
            
        logger.info(f"🔄 Token needs refresh (expires within 5 minutes), refreshing now...")
        
        try:
            # Create credentials object for refresh
            logger.debug("🔑 Creating credentials object for token refresh")
            creds = Credentials(
                token=tokens.access_token,
                refresh_token=tokens.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.client_id,
                client_secret=self.client_secret,
            )
            
            # Refresh the token
            logger.info("🌐 Making token refresh request to Google...")
            creds.refresh(Request())
            logger.info("✅ Token refresh request successful")
            
            # Update tokens in database
            new_expires_at = datetime.now(timezone.utc) + timedelta(seconds=3600)
            logger.info(f"💾 Saving refreshed token, new expiry: {new_expires_at}")
            
            if self._save_tokens_to_db(
                access_token=creds.token,
                refresh_token=tokens.refresh_token,  # Keep the same refresh token
                expires_at=new_expires_at,
                scope=tokens.scope or " ".join(self.scopes)
            ):
                logger.info(f"✅ Token refreshed successfully for user {self.user_id}")
                return True
            else:
                logger.error(f"❌ Failed to save refreshed token for user {self.user_id}")
                return False
            
        except Exception as e:
            logger.error(f"❌ Failed to refresh token for user {self.user_id}: {str(e)}")
            return False

    def get_token_info(self) -> dict:
        """Get token information including expiry"""
        tokens = self._get_tokens_from_db()
        if not tokens:
            return {"authenticated": False}
            
        # Handle timezone consistency for token info
        now = datetime.now(timezone.utc)
        expires_at = self._ensure_utc(tokens.expires_at)
            
        return {
            "authenticated": True,
            "expires_at": expires_at.isoformat(),
            "expires_in_seconds": int((expires_at - now).total_seconds()),
            "needs_refresh": now >= (expires_at - timedelta(minutes=5)),
            "provider": tokens.provider,
            "user_id": str(tokens.user_id)
        }
