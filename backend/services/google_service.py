import os
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, List
from uuid import UUID
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from dotenv import load_dotenv
from database import get_supabase
from models import OAuthToken, Email, EmailAttachment

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

    def _extract_email_details(self, msg_data: dict) -> dict:
        """Extract detailed information from Gmail message data"""
        logger.debug(f"📝 Extracting details for email ID: {msg_data.get('id')}")
        
        # Get basic info
        email_id = msg_data.get('id')
        thread_id = msg_data.get('threadId')
        snippet = msg_data.get('snippet', '')
        
        # Get headers
        headers = {}
        payload = msg_data.get('payload', {})
        for header in payload.get('headers', []):
            headers[header['name'].lower()] = header['value']
        
        # Extract common header fields
        subject = headers.get('subject', 'No Subject')
        from_email = headers.get('from', 'Unknown Sender')
        to_email = headers.get('to', 'Unknown Recipient')
        date = headers.get('date', '')
        
        # Get email body
        body_text = self._extract_body(payload)
        
        # Check if email has attachments
        has_attachments = self._has_attachments(payload)
        
        # Get labels
        labels = msg_data.get('labelIds', [])
        
        email_details = {
            'id': email_id,
            'thread_id': thread_id,
            'subject': subject,
            'from': from_email,
            'to': to_email,
            'date': date,
            'snippet': snippet,
            'body': body_text,
            'labels': labels,
            'has_attachments': has_attachments,
            'size_estimate': msg_data.get('sizeEstimate', 0)
        }
        
        logger.debug(f"✅ Extracted email: {subject[:50]}... from {from_email}")
        return email_details

    def _extract_body(self, payload: dict) -> dict:
        """Extract email body (both plain text and HTML if available)"""
        body = {
            'text': '',
            'html': ''
        }
        
        def extract_part_data(part):
            """Recursively extract data from message parts"""
            mime_type = part.get('mimeType', '')
            
            if mime_type == 'text/plain':
                data = part.get('body', {}).get('data', '')
                if data:
                    import base64
                    try:
                        decoded = base64.urlsafe_b64decode(data).decode('utf-8')
                        body['text'] = decoded
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to decode plain text body: {str(e)}")
                        
            elif mime_type == 'text/html':
                data = part.get('body', {}).get('data', '')
                if data:
                    import base64
                    try:
                        decoded = base64.urlsafe_b64decode(data).decode('utf-8')
                        body['html'] = decoded
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to decode HTML body: {str(e)}")
            
            # Recursively check parts
            if 'parts' in part:
                for subpart in part['parts']:
                    extract_part_data(subpart)
        
        # Start extraction
        if 'parts' in payload:
            for part in payload['parts']:
                extract_part_data(part)
        else:
            # Single part message
            extract_part_data(payload)
        
        return body

    def _has_attachments(self, payload: dict) -> bool:
        """Check if email has attachments"""
        def check_parts(part):
            # Check if this part is an attachment
            if part.get('filename') and part.get('body', {}).get('attachmentId'):
                return True
            
            # Check nested parts
            if 'parts' in part:
                for subpart in part['parts']:
                    if check_parts(subpart):
                        return True
            return False
        
        if 'parts' in payload:
            for part in payload['parts']:
                if check_parts(part):
                    return True
        
        return False

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

    def _save_email_to_db(self, email_data: dict) -> bool:
        """Save email to database"""
        if not self.user_id:
            logger.warning("❌ No user_id provided, cannot save email")
            return False
        
        try:
            # Parse date_sent if it exists
            date_sent = None
            if email_data.get('date'):
                try:
                    from email.utils import parsedate_to_datetime
                    date_sent = parsedate_to_datetime(email_data['date'])
                    # Ensure timezone-aware
                    if date_sent.tzinfo is None:
                        date_sent = date_sent.replace(tzinfo=timezone.utc)
                    else:
                        date_sent = date_sent.astimezone(timezone.utc)
                except Exception as e:
                    logger.warning(f"⚠️ Failed to parse email date '{email_data.get('date')}': {str(e)}")
            
            # Prepare email data for database
            db_email_data = {
                "user_id": str(self.user_id),
                "gmail_id": email_data['id'],
                "thread_id": email_data.get('thread_id'),
                "subject": email_data.get('subject'),
                "from_email": email_data.get('from'),
                "to_email": email_data.get('to'),
                "date_sent": date_sent.isoformat() if date_sent else None,
                "snippet": email_data.get('snippet'),
                "body_text": email_data.get('body', {}).get('text'),
                "body_html": email_data.get('body', {}).get('html'),
                "labels": email_data.get('labels', []),
                "has_attachments": email_data.get('has_attachments', False),
                "size_estimate": email_data.get('size_estimate')
            }
            
            # Remove None values to avoid database issues
            db_email_data = {k: v for k, v in db_email_data.items() if v is not None}
            
            logger.debug(f"💾 Saving email to database: {email_data.get('subject', 'No Subject')[:50]}...")
            
            # Try to insert or update (upsert)
            result = self.supabase.table("emails").upsert(
                db_email_data,
                on_conflict="user_id,gmail_id"  # Handle duplicates
            ).execute()
            
            if result.data:
                logger.info(f"✅ Successfully saved email {email_data['id']} to database")
                return True
            else:
                logger.warning(f"⚠️ No data returned when saving email {email_data['id']}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error saving email {email_data.get('id', 'unknown')} to database: {str(e)}")
            return False

    def _get_emails_from_db(self, limit: int = 10) -> List[dict]:
        """Retrieve emails from database for the current user"""
        if not self.user_id:
            logger.warning("❌ No user_id provided, cannot retrieve emails")
            return []
        
        try:
            logger.info(f"🔍 Retrieving {limit} emails from database for user {self.user_id}")
            
            result = self.supabase.table("emails").select("*").eq("user_id", str(self.user_id)).order("date_sent", desc=True).limit(limit).execute()
            
            if result.data:
                logger.info(f"✅ Found {len(result.data)} emails in database for user {self.user_id}")
                return result.data
            else:
                logger.info(f"🔍 No emails found in database for user {self.user_id}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Error retrieving emails from database for user {self.user_id}: {str(e)}")
            return []

    def get_inbox_emails(self, limit: int = 50, offset: int = 0) -> List[dict]:
        """Get inbox emails with pagination and enhanced formatting"""
        if not self.user_id:
            logger.warning("❌ No user_id provided, cannot retrieve inbox")
            return []
        
        try:
            logger.info(f"📥 Retrieving inbox for user {self.user_id} (limit: {limit}, offset: {offset})")
            
            # Query emails with pagination, ordered by date (newest first)
            result = self.supabase.table("emails").select(
                "id, gmail_id, subject, from_email, to_email, date_sent, snippet, "
                "labels, has_attachments, size_estimate, is_processed, created_at"
            ).eq("user_id", str(self.user_id)).order("date_sent", desc=True).range(offset, offset + limit - 1).execute()
            
            if result.data:
                # Format emails for inbox display
                formatted_emails = []
                for email in result.data:
                    formatted_email = self._format_inbox_email(email)
                    formatted_emails.append(formatted_email)
                
                logger.info(f"✅ Retrieved {len(formatted_emails)} emails for inbox")
                return formatted_emails
            else:
                logger.info(f"📭 No emails found in inbox for user {self.user_id}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Error retrieving inbox for user {self.user_id}: {str(e)}")
            return []

    def _format_inbox_email(self, email: dict) -> dict:
        """Format email for inbox display"""
        # Parse date for better display
        date_sent = email.get('date_sent')
        formatted_date = None
        if date_sent:
            try:
                from datetime import datetime
                if isinstance(date_sent, str):
                    parsed_date = datetime.fromisoformat(date_sent.replace('Z', '+00:00'))
                    formatted_date = parsed_date.strftime('%Y-%m-%d %H:%M')
                else:
                    formatted_date = date_sent.strftime('%Y-%m-%d %H:%M')
            except Exception as e:
                logger.warning(f"⚠️ Failed to format date {date_sent}: {str(e)}")
                formatted_date = str(date_sent) if date_sent else None

        # Extract sender name from email address
        from_email = email.get('from_email', '')
        sender_name = from_email
        if '<' in from_email and '>' in from_email:
            # Extract name from "Name <email@domain.com>" format
            sender_name = from_email.split('<')[0].strip().strip('"')
            if not sender_name:
                sender_name = from_email.split('<')[1].split('>')[0]
        
        # Determine email status
        labels = email.get('labels', [])
        is_unread = 'UNREAD' in labels
        is_important = 'IMPORTANT' in labels
        is_starred = 'STARRED' in labels
        
        return {
            'id': email.get('id'),
            'gmail_id': email.get('gmail_id'),
            'subject': email.get('subject') or '(No Subject)',
            'sender': sender_name,
            'from_email': from_email,
            'date': formatted_date,
            'date_sent': date_sent,
            'snippet': email.get('snippet', '')[:150] + '...' if email.get('snippet', '') else '',
            'labels': labels,
            'has_attachments': email.get('has_attachments', False),
            'size_estimate': email.get('size_estimate'),
            'is_unread': is_unread,
            'is_important': is_important,
            'is_starred': is_starred,
            'is_processed': email.get('is_processed', False),
            'created_at': email.get('created_at')
        }

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

    def fetch_gmail_emails(self, max_results: int = 10) -> list:
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
            logger.info(f"🌐 Fetching messages from Gmail API (max {max_results})")
            result = service.users().messages().list(
                userId='me', 
                maxResults=max_results
            ).execute()
            
            messages = result.get('messages', [])
            logger.info(f"📨 Found {len(messages)} messages")
            
            emails = []
            
            for i, msg in enumerate(messages):
                logger.debug(f"📧 Fetching details for message {i+1}/{len(messages)}: {msg['id']}")
                msg_data = service.users().messages().get(
                    userId='me', 
                    id=msg['id'],
                    format='full'  # Get full message details including body
                ).execute()
                
                # Extract email details
                email_details = self._extract_email_details(msg_data)
                emails.append(email_details)
                
                # Save email to database
                self._save_email_to_db(email_details)
            
            logger.info(f"✅ Successfully fetched and saved {len(emails)} emails for user {self.user_id}")
            return emails
            
        except Exception as e:
            logger.error(f"❌ Error fetching emails for user {self.user_id}: {str(e)}")
            return []

    def get_single_email(self, email_id: str) -> dict:
        """Get detailed information for a single email by ID"""
        logger.info(f"📧 Fetching single email {email_id} for user {self.user_id}")
        
        # Get tokens from database
        tokens = self._get_tokens_from_db()
        if not tokens:
            logger.warning(f"❌ No tokens available for user {self.user_id}")
            return {"error": "No authentication tokens available"}

        try:
            # Check if token needs refresh
            if not self._refresh_token_if_needed():
                logger.error(f"❌ Token refresh failed for user {self.user_id}")
                return {"error": "Token refresh failed"}
            
            # Get fresh tokens after potential refresh
            tokens = self._get_tokens_from_db()
            if not tokens:
                logger.error(f"❌ No tokens found after refresh for user {self.user_id}")
                return {"error": "No tokens found after refresh"}

            # Build credentials object
            creds_obj = Credentials(
                tokens.access_token,
                refresh_token=tokens.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.client_id,
                client_secret=self.client_secret,
            )
            
            # Build Gmail service
            service = build('gmail', 'v1', credentials=creds_obj)
            
            # Fetch single message
            logger.info(f"🌐 Fetching email details for ID: {email_id}")
            msg_data = service.users().messages().get(
                userId='me', 
                id=email_id,
                format='full'
            ).execute()
            
            # Extract email details
            email_details = self._extract_email_details(msg_data)
            
            logger.info(f"✅ Successfully fetched email: {email_details.get('subject', 'No Subject')}")
            return email_details
            
        except Exception as e:
            logger.error(f"❌ Error fetching email {email_id} for user {self.user_id}: {str(e)}")
            return {"error": f"Failed to fetch email: {str(e)}"}

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
