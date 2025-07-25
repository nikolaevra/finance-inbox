import os
import logging
import re
import base64
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Union
from uuid import UUID
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from dotenv import load_dotenv
from database import get_supabase
from models import OAuthToken, EmailDetails, ConnectionProvider

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

class GoogleService:
    def __init__(self, internal_user_id: Optional[Union[str, UUID]] = None):
        self.client_id = os.environ["GOOGLE_CLIENT_ID"]
        self.client_secret = os.environ["GOOGLE_CLIENT_SECRET"]
        self.redirect_uri = os.environ["GOOGLE_REDIRECT_URI"]
        self.internal_user_id = str(internal_user_id) if internal_user_id else None  # Internal user ID from users table
        self.scopes = [
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/gmail.send",
            "openid",
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile"
        ]
        self.supabase = get_supabase()
        
        # Log initialization
        if self.internal_user_id:
            logger.info(f"🔧 GoogleService initialized for internal_user_id: {self.internal_user_id}")
        else:
            logger.warning("⚠️ GoogleService initialized without internal_user_id")

    def _ensure_utc(self, dt: datetime) -> datetime:
        """Ensure a datetime is in UTC timezone"""
        if dt.tzinfo is None:
            # Naive datetime, assume it's UTC
            return dt.replace(tzinfo=timezone.utc)
        else:
            # Convert to UTC if it's in a different timezone
            return dt.astimezone(timezone.utc)

    def _extract_email_details(self, msg_data: dict) -> EmailDetails:
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
        
        email_details = EmailDetails(
            id=email_id,
            thread_id=thread_id,
            subject=subject,
            from_email=from_email,
            to_email=to_email,
            date=date,
            snippet=snippet,
            body=body_text,
            labels=labels,
            has_attachments=has_attachments,
            size_estimate=msg_data.get('sizeEstimate', 0)
        )
        
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
            
            if mime_type == 'text/plain' and not body['text']:
                data = part.get('body', {}).get('data', '')
                if data:
                    try:
                        decoded = base64.urlsafe_b64decode(data + '===').decode('utf-8')
                        body['text'] = decoded
                        logger.debug(f"✅ Extracted plain text body ({len(decoded)} chars)")
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to decode plain text body: {str(e)}")
                        
            elif mime_type == 'text/html' and not body['html']:
                data = part.get('body', {}).get('data', '')
                if data:
                    try:
                        decoded = base64.urlsafe_b64decode(data + '===').decode('utf-8')
                        body['html'] = decoded
                        logger.debug(f"✅ Extracted HTML body ({len(decoded)} chars)")
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
        
        # Log what we found
        has_text = bool(body['text'])
        has_html = bool(body['html'])
        logger.debug(f"📝 Body extraction complete - Text: {'✅' if has_text else '❌'}, HTML: {'✅' if has_html else '❌'}")
        
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
        """Retrieve tokens from database through connections table"""
        logger.info(f"🔍 Retrieving tokens for internal_user_id: {self.internal_user_id}")
        
        if not self.internal_user_id:
            logger.warning("❌ No internal_user_id available, cannot retrieve tokens")
            return None
            
        try:
            # First, get the Gmail connection for this user
            logger.debug(f"📊 Looking up Gmail connection for user_id: {self.internal_user_id}")
            connection_result = self.supabase.table("connections").select("oauth_token_id").eq("user_id", str(self.internal_user_id)).eq("connection_provider", "gmail").single().execute()
            
            if not connection_result.data or not connection_result.data.get('oauth_token_id'):
                logger.info(f"🔍 No Gmail connection or oauth_token_id found for user {self.internal_user_id}")
                return None
            
            oauth_token_id = connection_result.data['oauth_token_id']
            logger.debug(f"📊 Found oauth_token_id: {oauth_token_id}, retrieving token details")
            
            # Now get the OAuth token using the ID from connection
            token_result = self.supabase.table("oauth_tokens").select("*").eq("id", oauth_token_id).eq("provider", "google").single().execute()
            
            if token_result.data:
                token = OAuthToken(**token_result.data)
                logger.info(f"✅ Found tokens for user {self.internal_user_id}, expires at: {token.expires_at}")
                return token
            else:
                logger.info(f"🔍 No OAuth token found with ID {oauth_token_id}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error retrieving tokens for user {self.internal_user_id}: {str(e)}")
            return None

    def _save_tokens_to_db(self, access_token: str, refresh_token: str, expires_at: datetime, scope: str) -> bool:
        """Save or update tokens in database through connections table"""
        logger.info(f"💾 Saving tokens for user_id: {self.internal_user_id}, expires at: {expires_at}")
        
        if not self.internal_user_id:
            logger.warning("❌ No internal_user_id available, cannot save tokens")
            return False
            
        try:
            # Ensure expires_at is always stored in UTC
            expires_at_utc = self._ensure_utc(expires_at)
            
            token_data = {
                "provider": "google",
                "access_token": access_token,
                "refresh_token": refresh_token,
                "expires_at": expires_at_utc.isoformat(),
                "scope": scope
            }
            
            logger.debug(f"📅 Storing expiry time in UTC: {expires_at_utc.isoformat()}")
            logger.debug(f"📝 Token data prepared: provider=google, expires_at={expires_at_utc.isoformat()}")
            
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
                connection_update = self.supabase.table("connections").update({
                    "oauth_token_id": oauth_token_id,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }).eq("user_id", str(self.internal_user_id)).eq("connection_provider", "gmail").execute()
                
                if not connection_update.data:
                    logger.warning("⚠️ Failed to update connection with oauth_token_id")
            
            success = len(result.data) > 0 if result.data else False
            if success:
                logger.info(f"✅ Successfully saved tokens for user {self.internal_user_id}")
            else:
                logger.warning(f"⚠️ No data returned when saving tokens for user {self.internal_user_id}")
                
            return success
        except Exception as e:
            logger.error(f"❌ Error saving tokens for user {self.internal_user_id}: {str(e)}")
            return False

    def _delete_tokens_from_db(self) -> bool:
        """Delete tokens from database through connections table"""
        if not self.internal_user_id:
            return False
            
        try:
            # Get the oauth_token_id from the connection
            existing_token = self._get_tokens_from_db()
            if not existing_token:
                logger.info("🔍 No tokens found to delete")
                return True  # Nothing to delete is success
            
            # Delete the OAuth token
            result = self.supabase.table("oauth_tokens").delete().eq("id", existing_token.id).execute()
            
            # Clear the oauth_token_id from the connection
            self.supabase.table("connections").update({
                "oauth_token_id": None,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }).eq("user_id", str(self.internal_user_id)).eq("connection_provider", "gmail").execute()
            
            logger.info("✅ Successfully deleted tokens and cleared connection reference")
            return True
        except Exception as e:
            logger.error(f"❌ Error deleting tokens: {str(e)}")
            return False

    def _create_gmail_connection(self) -> bool:
        """Create Gmail connection record after successful OAuth"""
        if not self.internal_user_id:
            logger.warning("❌ No internal_user_id available, cannot create connection record")
            return False
        
        try:
            # Import here to avoid circular imports
            from services.connections_service import connections_service
            
            # Get the OAuth token ID from the database
            tokens = self._get_tokens_from_db()
            oauth_token_id = str(tokens.id) if tokens and tokens.id else None
            
            # Use the connections service to handle Gmail connection creation
            return connections_service.create_gmail_connection_after_oauth(
                user_id=str(self.internal_user_id),
                oauth_token_id=oauth_token_id,
                scopes=self.scopes
            )
                
        except Exception as e:
            logger.error(f"❌ Error creating Gmail connection: {str(e)}")
            return False

    def _update_last_sync(self) -> bool:
        """Update last sync timestamp for Gmail connection"""
        if not self.internal_user_id:
            return False
        
        try:
            # Import here to avoid circular imports
            from services.connections_service import connections_service
            
            return connections_service.update_last_sync(
                user_id=str(self.internal_user_id),
                provider=ConnectionProvider.GMAIL
            )
        except Exception as e:
            logger.error(f"❌ Error updating last sync: {str(e)}")
            return False

    def _save_email_to_db(self, email_data: EmailDetails) -> bool:
        """Save email to database with categorization"""
        if not self.internal_user_id:
            logger.warning("❌ No internal_user_id available, cannot save email")
            return False
        
        try:
            # Parse date_sent if it exists
            date_sent = None
            if email_data.date:
                try:
                    from email.utils import parsedate_to_datetime
                    date_sent = parsedate_to_datetime(email_data.date)
                    # Ensure timezone-aware
                    if date_sent.tzinfo is None:
                        date_sent = date_sent.replace(tzinfo=timezone.utc)
                    else:
                        date_sent = date_sent.astimezone(timezone.utc)
                except Exception as e:
                    logger.warning(f"⚠️ Failed to parse email date '{email_data.date}': {str(e)}")
            
            # Prepare email data for database
            db_email_data = {
                "user_id": str(self.internal_user_id),
                "gmail_id": email_data.id,
                "thread_id": email_data.thread_id,
                "subject": email_data.subject,
                "from_email": email_data.from_email,
                "to_email": email_data.to_email,
                "date_sent": date_sent.isoformat() if date_sent else None,
                "snippet": email_data.snippet,
                "body_text": email_data.body.get('text'),
                "body_html": email_data.body.get('html'),
                "labels": email_data.labels,
                "has_attachments": email_data.has_attachments,
                "size_estimate": email_data.size_estimate,
                "is_read": False  # New emails are always unread
            }
            
            # Add CC and BCC fields if available (for sent emails)
            if email_data.cc_email:
                db_email_data['cc_email'] = email_data.cc_email
            if email_data.bcc_email:
                db_email_data['bcc_email'] = email_data.bcc_email
            
            # Add email categorization using LLM
            try:
                from services.email_categorization_service import get_email_categorization_service
                categorization_service = get_email_categorization_service()
                categorization_result = categorization_service.categorize_email_with_metadata(db_email_data, str(self.internal_user_id))
                
                # Add categorization fields to database data
                if categorization_result['category']:
                    db_email_data['category'] = categorization_result['category']
                    db_email_data['category_confidence'] = categorization_result['category_confidence']
                    db_email_data['categorized_at'] = categorization_result['categorized_at'].isoformat()
                    db_email_data['category_prompt_version'] = categorization_result['category_prompt_version']
                    
                    logger.info(f"✅ Email categorized as: {categorization_result['category']} (confidence: {categorization_result['category_confidence']})")
                else:
                    logger.warning("⚠️ Email categorization failed - no category returned")
                    
            except Exception as e:
                logger.error(f"❌ Email categorization failed: {str(e)}")
                # Continue saving email even if categorization fails
            
            # Remove None values to avoid database issues
            db_email_data = {k: v for k, v in db_email_data.items() if v is not None}
            
            logger.debug(f"💾 Saving email to database: {email_data.subject[:50]}...")
            
            # Try to insert or update (upsert)
            result = self.supabase.table("emails").upsert(
                db_email_data,
                on_conflict="user_id,gmail_id"  # Handle duplicates
            ).execute()
            
            if result.data:
                logger.info(f"✅ Successfully saved email {email_data.id} to database")
                return True
            else:
                logger.warning(f"⚠️ No data returned when saving email {email_data.id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error saving email {email_data.id} to database: {str(e)}")
            return False

    def _get_emails_from_db(self, limit: int = 10) -> List[dict]:
        """Retrieve emails from database for the current user"""
        if not self.internal_user_id:
            logger.warning("❌ No internal_user_id available, cannot retrieve emails")
            return []
        
        try:
            logger.info(f"🔍 Retrieving {limit} emails from database for user {self.internal_user_id}")
            
            result = self.supabase.table("emails").select("*").eq("user_id", str(self.internal_user_id)).order("date_sent", desc=True).limit(limit).execute()
            
            if result.data:
                logger.info(f"✅ Found {len(result.data)} emails in database for user {self.internal_user_id}")
                return result.data
            else:
                logger.info(f"🔍 No emails found in database for user {self.internal_user_id}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Error retrieving emails from database for user {self.internal_user_id}: {str(e)}")
            return []

    def _get_most_recent_email_date(self) -> Optional[datetime]:
        """Get the date of the most recent email in the database"""
        if not self.internal_user_id:
            return None
        
        try:
            result = self.supabase.table("emails").select("date_sent").eq("user_id", str(self.internal_user_id)).order("date_sent", desc=True).limit(1).execute()
            
            if result.data and result.data[0].get('date_sent'):
                # Parse the date string back to datetime
                from dateutil.parser import parse
                return parse(result.data[0]['date_sent'])
            return None
        except Exception as e:
            logger.error(f"❌ Error getting most recent email date: {str(e)}")
            return None

    def _email_exists_in_db(self, gmail_id: str) -> bool:
        """Check if an email already exists in the database"""
        if not self.internal_user_id:
            return False
        
        try:
            result = self.supabase.table("emails").select("id").eq("user_id", str(self.internal_user_id)).eq("gmail_id", gmail_id).execute()
            return bool(result.data)
        except Exception as e:
            logger.error(f"❌ Error checking if email exists: {str(e)}")
            return False

    def mark_email_as_read(self, email_id: str) -> bool:
        """Mark a single email as read"""
        if not self.internal_user_id:
            return False
        
        try:
            result = self.supabase.table("emails").update({"is_read": True}).eq("user_id", str(self.internal_user_id)).eq("id", email_id).execute()
            return bool(result.data)
        except Exception as e:
            logger.error(f"❌ Error marking email as read: {str(e)}")
            return False

    def mark_thread_as_read(self, thread_id: str) -> int:
        """Mark all emails in a thread as read"""
        if not self.internal_user_id:
            return 0
        
        try:
            result = self.supabase.table("emails").update({"is_read": True}).eq("user_id", str(self.internal_user_id)).eq("thread_id", thread_id).execute()
            return len(result.data) if result.data else 0
        except Exception as e:
            logger.error(f"❌ Error marking thread as read: {str(e)}")
            return 0

    def get_inbox_emails(self, limit: int = 50, offset: int = 0) -> List[dict]:
        """Get inbox emails with pagination and enhanced formatting"""
        if not self.internal_user_id:
            logger.warning("❌ No internal_user_id available, cannot retrieve inbox")
            return []
        
        try:
            logger.info(f"📥 Retrieving inbox for user {self.internal_user_id} (limit: {limit}, offset: {offset})")
            
            # Query emails with pagination, ordered by date (newest first)
            result = self.supabase.table("emails").select(
                "id, gmail_id, subject, from_email, to_email, date_sent, snippet, "
                "labels, has_attachments, size_estimate, is_processed, created_at, "
                "category, category_confidence, categorized_at, category_prompt_version, is_read"
            ).eq("user_id", str(self.internal_user_id)).order("date_sent", desc=True).range(offset, offset + limit - 1).execute()
            
            if result.data:
                # Format emails for inbox display
                formatted_emails = []
                for email in result.data:
                    formatted_email = self._format_inbox_email(email)
                    formatted_emails.append(formatted_email)
                
                logger.info(f"✅ Retrieved {len(formatted_emails)} emails for inbox")
                return formatted_emails
            else:
                logger.info(f"📭 No emails found in inbox for user {self.internal_user_id}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Error retrieving inbox for user {self.internal_user_id}: {str(e)}")
            return []

    def get_inbox_threads(self, limit: int = 50, offset: int = 0) -> List[dict]:
        """Get inbox organized by email threads with proper ordering"""
        if not self.internal_user_id:
            logger.warning("❌ No internal_user_id available, cannot retrieve inbox threads")
            return []
        
        try:
            logger.info(f"🧵 Retrieving inbox threads for user {self.internal_user_id} (limit: {limit}, offset: {offset})")
            
            # Get all emails for the user, including thread_id
            result = self.supabase.table("emails").select(
                "id, gmail_id, subject, from_email, to_email, date_sent, snippet, "
                "labels, has_attachments, size_estimate, is_processed, created_at, thread_id, "
                "category, category_confidence, categorized_at, category_prompt_version, is_read"
            ).eq("user_id", str(self.internal_user_id)).order("date_sent", desc=True).execute()
            
            if not result.data:
                logger.info(f"📭 No emails found for user {self.internal_user_id}")
                return []
            
            # Group emails by thread_id
            threads_map = {}
            for email in result.data:
                thread_id = email.get('thread_id')
                if not thread_id:
                    # If no thread_id, create a single-email thread using gmail_id
                    thread_id = email.get('gmail_id', f"single_{email.get('id')}")
                
                if thread_id not in threads_map:
                    threads_map[thread_id] = []
                
                formatted_email = self._format_inbox_email(email)
                formatted_email['thread_id'] = thread_id  # Ensure thread_id is included
                threads_map[thread_id].append(formatted_email)
            
            # Convert to list of thread objects and sort
            threads = []
            for thread_id, emails in threads_map.items():
                # Sort emails within thread by date (oldest first for conversation flow)
                # Use a very old date as fallback for None/empty date_sent to ensure consistent sorting
                emails.sort(key=lambda x: x.get('date_sent') or '1970-01-01T00:00:00Z', reverse=False)
                
                # Get thread metadata from the latest email
                latest_email = max(emails, key=lambda x: x.get('date_sent') or '1970-01-01T00:00:00Z')
                
                # Count unread emails in thread
                unread_count = sum(1 for email in emails if email.get('is_unread', False))
                
                # Determine if thread has attachments
                has_attachments = any(email.get('has_attachments', False) for email in emails)
                
                # Create thread object
                thread = {
                    'thread_id': thread_id,
                    'subject': latest_email.get('subject', '(No Subject)'),
                    'latest_sender': latest_email.get('sender', 'Unknown'),
                    'latest_from_email': latest_email.get('from_email', ''),
                    'latest_date': latest_email.get('date'),
                    'latest_date_sent': latest_email.get('date_sent'),
                    'latest_snippet': latest_email.get('snippet', ''),
                    'email_count': len(emails),
                    'unread_count': unread_count,
                    'has_attachments': has_attachments,
                    'is_unread': unread_count > 0,
                    'labels': latest_email.get('labels', []),
                    'emails': emails  # All emails in the thread
                }
                
                threads.append(thread)
            
            # Sort threads by latest email date (newest first)
            # Use a very old date as fallback for None/empty date_sent to ensure consistent sorting
            threads.sort(key=lambda x: x.get('latest_date_sent') or '1970-01-01T00:00:00Z', reverse=True)
            
            # Apply pagination to threads
            paginated_threads = threads[offset:offset + limit]
            
            logger.info(f"✅ Retrieved {len(paginated_threads)} threads (total: {len(threads)}) for inbox")
            return paginated_threads
                
        except Exception as e:
            logger.error(f"❌ Error retrieving inbox threads for user {self.internal_user_id}: {str(e)}")
            return []

    def get_thread_by_id(self, thread_id: str) -> Optional[dict]:
        """Get a specific thread by thread_id with all emails"""
        if not self.internal_user_id:
            logger.warning("❌ No internal_user_id available, cannot retrieve thread")
            return None
        
        try:
            logger.info(f"🧵 Retrieving thread {thread_id} for user {self.internal_user_id}")
            
            # Get all emails in the thread
            result = self.supabase.table("emails").select("*").eq("user_id", str(self.internal_user_id)).eq("thread_id", thread_id).order("date_sent", desc=False).execute()
            
            if not result.data:
                logger.info(f"📭 No emails found in thread {thread_id}")
                return None
            
            # Format all emails in the thread
            formatted_emails = []
            for email in result.data:
                formatted_email = self._format_full_email(email)
                formatted_emails.append(formatted_email)
            
            # Get thread metadata from the latest email
            latest_email = max(formatted_emails, key=lambda x: x.get('date_sent') or '1970-01-01T00:00:00Z')
            
            # Count unread emails in thread
            unread_count = sum(1 for email in formatted_emails if email.get('is_unread', False))
            
            # Determine if thread has attachments
            has_attachments = any(email.get('has_attachments', False) for email in formatted_emails)
            
            thread = {
                'thread_id': thread_id,
                'subject': latest_email.get('subject', '(No Subject)'),
                'latest_sender': latest_email.get('sender', 'Unknown'),
                'latest_from_email': latest_email.get('from_email', ''),
                'latest_date': latest_email.get('date'),
                'latest_date_sent': latest_email.get('date_sent'),
                'email_count': len(formatted_emails),
                'unread_count': unread_count,
                'has_attachments': has_attachments,
                'is_unread': unread_count > 0,
                'labels': latest_email.get('labels', []),
                'emails': formatted_emails  # All emails with full content
            }
            
            logger.info(f"✅ Retrieved thread {thread_id} with {len(formatted_emails)} emails")
            return thread
                
        except Exception as e:
            logger.error(f"❌ Error retrieving thread {thread_id}: {str(e)}")
            return None

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
        is_unread = not email.get('is_read', False)
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
            'created_at': email.get('created_at'),
            # Email categorization fields
            'category': email.get('category'),
            'category_confidence': email.get('category_confidence'),
            'categorized_at': email.get('categorized_at'),
            'category_prompt_version': email.get('category_prompt_version')
        }

    def _format_full_email(self, email: dict) -> dict:
        """Format email for full display including body content"""
        # Start with inbox formatting
        formatted_email = self._format_inbox_email(email)
        
        # Add body content for full email view
        body_text = email.get('body_text', '')
        body_html = email.get('body_html', '')
        
        # Format body object to match frontend expectations
        formatted_email['body'] = {
            'text': body_text,
            'html': body_html
        }
        
        # Add additional fields for full email view
        formatted_email.update({
            'to_email': email.get('to_email'),
            'cc_email': email.get('cc_email'),
            'bcc_email': email.get('bcc_email'),
            'reply_to': email.get('reply_to'),
            'thread_id': email.get('thread_id'),
            'full_snippet': email.get('snippet', ''),  # Full snippet without truncation
        })
        
        return formatted_email

    def get_authorization_url(self, state: str = None) -> str:
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
        
        auth_params = {
            'access_type': 'offline',
            'include_granted_scopes': 'true',
            'prompt': 'consent'  # Force consent screen to get refresh token
        }
        
        # Add custom state if provided (for user identification in callback)
        if state:
            auth_params['state'] = state
        
        authorization_url, _ = flow.authorization_url(**auth_params)

        return authorization_url

    def handle_oauth_callback(self, code: str) -> dict:
        """Handle OAuth callback and store tokens"""
        logger.info(f"🔐 Handling OAuth callback for user {self.internal_user_id}")
        
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
            
            logger.info(f"💾 Attempting to save tokens for user {self.internal_user_id}, expires at: {expires_at}")
            
            # Save tokens to database
            if self._save_tokens_to_db(
                access_token=credentials.token,
                refresh_token=credentials.refresh_token or "",  # Handle None refresh token
                expires_at=expires_at,
                scope=scope_string
            ):
                logger.info(f"✅ OAuth flow completed successfully for user {self.internal_user_id}")
                
                # Create/update connection record
                self._create_gmail_connection()
                
                return {"message": "Authentication complete. Tokens saved to database."}
            else:
                logger.error(f"❌ Failed to save tokens to database for user {self.internal_user_id}")
                return {"error": "Failed to save tokens to database"}
                
        except Exception as e:
            logger.error(f"❌ OAuth callback failed for user {self.internal_user_id}: {str(e)}")
            return {"error": f"Authentication failed: {str(e)}"}

    def fetch_gmail_emails(self, max_results: int = 10, only_new: bool = False) -> list:
        """Fetch Gmail emails using stored credentials
        
        Args:
            max_results: Maximum number of emails to fetch
            only_new: If True, only fetch emails that don't exist in database
        """
        logger.info(f"📧 Starting Gmail email fetch for user {self.internal_user_id} (only_new={only_new})")
        
        # Get authenticated Gmail service
        service, error = self._get_authenticated_gmail_service()
        if error:
            logger.error(f"❌ Cannot fetch emails: {error.get('error', 'Unknown error')}")
            return []

        try:
            # Build query for Gmail API
            query = ""
            if only_new:
                # Get the most recent email date from database
                last_email = self._get_most_recent_email_date()
                if last_email:
                    # Format date for Gmail API query
                    query = f"after:{last_email.strftime('%Y/%m/%d')}"
                    logger.info(f"🔍 Fetching emails newer than {last_email}")
            
            # Fetch messages
            logger.info(f"🌐 Fetching messages from Gmail API (max {max_results})")
            result = service.users().messages().list(
                userId='me', 
                maxResults=max_results,
                q=query if query else None
            ).execute()
            
            messages = result.get('messages', [])
            logger.info(f"📨 Found {len(messages)} messages")
            
            emails = []
            new_emails_count = 0
            
            for i, msg in enumerate(messages):
                # Check if email already exists in database
                if only_new and self._email_exists_in_db(msg['id']):
                    logger.debug(f"⏭️ Skipping existing email: {msg['id']}")
                    continue
                
                logger.debug(f"📧 Fetching details for message {i+1}/{len(messages)}: {msg['id']}")
                msg_data = service.users().messages().get(
                    userId='me', 
                    id=msg['id'],
                    format='full'  # Get full message details including body
                ).execute()
                
                # Extract email details
                email_details = self._extract_email_details(msg_data)
                emails.append(email_details.to_dict())  # Convert to dict for API compatibility
                
                # Save email to database
                if self._save_email_to_db(email_details):
                    new_emails_count += 1
            
            logger.info(f"✅ Successfully fetched and saved {new_emails_count} new emails for user {self.internal_user_id}")
            
            # Update last sync time
            self._update_last_sync()
            
            return emails
            
        except Exception as e:
            logger.error(f"❌ Error fetching emails for user {self.internal_user_id}: {str(e)}")
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
        """Clear stored tokens and disconnect connection"""
        try:
            # Import here to avoid circular imports
            from services.connections_service import connections_service
            
            # Disconnect the Gmail connection
            if self.internal_user_id:
                connections_service.disconnect_gmail_connection(str(self.internal_user_id))
            
            # Clear tokens from database
            if self._delete_tokens_from_db():
                return {"message": "Tokens cleared and connection disconnected"}
            else:
                return {"message": "Connection disconnected, but no tokens found or failed to clear"}
                
        except Exception as e:
            logger.error(f"❌ Error clearing tokens and connection: {str(e)}")
            return {"error": f"Failed to clear tokens: {str(e)}"}

    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        tokens = self._get_tokens_from_db()
        return bool(tokens and tokens.access_token)

    def _get_authenticated_gmail_service(self):
        """Get authenticated Gmail service object with token management"""
        logger.info(f"🔧 Getting authenticated Gmail service for user {self.internal_user_id}")
        
        # Get tokens from database
        tokens = self._get_tokens_from_db()
        if not tokens:
            logger.warning(f"❌ No tokens available for user {self.internal_user_id}")
            return None, {"error": "User not authenticated"}

        try:
            # Check if token needs refresh
            if not self._refresh_token_if_needed():
                logger.error(f"❌ Token refresh failed for user {self.internal_user_id}")
                return None, {"error": "Authentication failed"}
            
            # Get fresh tokens after potential refresh
            tokens = self._get_tokens_from_db()
            if not tokens:
                logger.error(f"❌ No tokens found after refresh for user {self.internal_user_id}")
                return None, {"error": "Authentication failed"}

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
            logger.info(f"✅ Gmail service authenticated successfully for user {self.internal_user_id}")
            
            return service, None
            
        except Exception as e:
            logger.error(f"❌ Error getting Gmail service for user {self.internal_user_id}: {str(e)}")
            return None, {"error": f"Authentication failed: {str(e)}"}

    def _refresh_token_if_needed(self) -> bool:
        """Refresh access token if it's expired or about to expire"""
        logger.info(f"🔄 Checking if token refresh is needed for user {self.internal_user_id}")
        
        tokens = self._get_tokens_from_db()
        if not tokens:
            logger.warning(f"❌ No tokens found for user {self.internal_user_id}")
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
            logger.info(f"✅ Token is still valid for user {self.internal_user_id} (expires in {time_until_expiry.total_seconds():.0f} seconds)")
            return True
        
        # Token needs refresh - NOW check if we have a refresh token
        if not tokens.refresh_token:
            logger.error(f"❌ Token expired/expiring but no refresh token available for user {self.internal_user_id}")
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
                logger.info(f"✅ Token refreshed successfully for user {self.internal_user_id}")
                return True
            else:
                logger.error(f"❌ Failed to save refreshed token for user {self.internal_user_id}")
                return False
            
        except Exception as e:
            logger.error(f"❌ Failed to refresh token for user {self.internal_user_id}: {str(e)}")
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
            "internal_user_id": str(self.internal_user_id)  # Use the service's internal_user_id instead
        }

    def get_single_email_from_db(self, email_id: str) -> Optional[dict]:
        """Get a single email from database by gmail_id with full body content"""
        if not self.internal_user_id:
            logger.warning("❌ No internal_user_id available, cannot retrieve email")
            return None
        
        try:
            logger.info(f"🔍 Retrieving email {email_id} from database for user {self.internal_user_id}")
            
            result = self.supabase.table("emails").select("*").eq("user_id", str(self.internal_user_id)).eq("gmail_id", email_id).single().execute()
            
            if result.data:
                # Format the email for full display (including body content)
                formatted_email = self._format_full_email(result.data)
                logger.info(f"✅ Found email in database: {formatted_email.get('subject', 'No Subject')}")
                return formatted_email
            else:
                logger.info(f"📭 No email found in database with ID {email_id}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error retrieving email {email_id} from database: {str(e)}")
            return None

    def send_email_reply(self, original_email_id: str, reply_body: str, reply_subject: str = None, 
                        to: Optional[List[str]] = None, cc: Optional[List[str]] = None, 
                        bcc: Optional[List[str]] = None) -> dict:
        """Send a reply to an email using Gmail API with customizable recipients"""
        logger.info(f"📤 Sending reply to email {original_email_id} for user {self.internal_user_id}")
        
        # Get authenticated Gmail service
        service, error = self._get_authenticated_gmail_service()
        if error:
            return error

        try:
            # Get original email data from our database (no API call needed!)
            logger.info(f"🔍 Getting original email {original_email_id} data from database")
            original_email = self.get_single_email_from_db(original_email_id)
            
            if not original_email:
                return {"error": f"Original email {original_email_id} not found in database"}
            
            # Extract data we need from our database
            original_subject = original_email.get('subject', 'No Subject')
            original_from = original_email.get('from_email', '')
            thread_id = original_email.get('thread_id', '')
            
            logger.info(f"✅ Retrieved original email data from database: {original_subject[:50]}...")
            
            # Determine recipients
            if to:
                # Use custom recipients if provided
                reply_to_emails = to
                logger.info(f"📧 Using custom TO recipients: {', '.join(reply_to_emails)}")
            else:
                # Default behavior: reply to original sender
                email_match = re.search(r'<(.+?)>', original_from)
                reply_to_email = email_match.group(1) if email_match else original_from
                reply_to_emails = [reply_to_email]
                logger.info(f"📧 Using default TO recipient: {reply_to_email}")
            
            # Get user's email address for 'from' field
            user_profile = service.users().getProfile(userId='me').execute()
            user_email = user_profile.get('emailAddress', '')
            
            # Prepare reply subject
            if not reply_subject:
                reply_subject = f"Re: {original_subject}" if not original_subject.startswith('Re:') else original_subject
            
            # Create the reply message
            msg = MIMEMultipart()
            msg['From'] = user_email
            msg['To'] = ', '.join(reply_to_emails)
            msg['Subject'] = reply_subject
            
            # Add CC recipients if provided
            if cc:
                msg['Cc'] = ', '.join(cc)
                logger.info(f"📧 Adding CC recipients: {', '.join(cc)}")
            
            # Add BCC recipients if provided (BCC is handled in the send request, not headers)
            if bcc:
                logger.info(f"📧 Adding BCC recipients: {', '.join(bcc)}")
            
            # Note: Gmail threading works primarily with threadId, so we don't need
            # the original message-id headers. Gmail will handle threading automatically.
            
            # Add the reply body
            msg.attach(MIMEText(reply_body, 'plain'))
            
            # Encode the message
            raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode('utf-8')
            
            # Prepare all recipients for Gmail API (TO + CC + BCC)
            all_recipients = reply_to_emails[:]
            if cc:
                all_recipients.extend(cc)
            if bcc:
                all_recipients.extend(bcc)
            
            # Send the reply
            logger.info(f"📤 Sending reply to {len(all_recipients)} recipients with subject: {reply_subject}")
            send_result = service.users().messages().send(
                userId='me',
                body={
                    'raw': raw_message,
                    'threadId': thread_id  # Keep it in the same thread
                }
            ).execute()
            
            sent_message_id = send_result.get('id')
            logger.info(f"✅ Reply sent successfully with ID: {sent_message_id}")
            
            # Store the sent email directly in database (no need to fetch from API)
            logger.info(f"💾 Storing sent email {sent_message_id} in database")
            try:
                # Create EmailDetails object from the data we already have
                sent_email_data = EmailDetails(
                    id=sent_message_id,
                    thread_id=thread_id,
                    subject=reply_subject,
                    from_email=user_email,
                    to_email=', '.join(reply_to_emails),
                    date=datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S %z'),
                    snippet=reply_body[:150] + '...' if len(reply_body) > 150 else reply_body,
                    body={'text': reply_body, 'html': ''},
                    labels=['SENT'],  # Gmail automatically adds SENT label
                    has_attachments=False,
                    size_estimate=len(reply_body),
                    cc_email=', '.join(cc) if cc else None,
                    bcc_email=', '.join(bcc) if bcc else None
                )
                
                # Save the sent email to database
                if self._save_email_to_db(sent_email_data):
                    logger.info(f"✅ Sent email {sent_message_id} stored in database")
                else:
                    logger.warning(f"⚠️ Failed to store sent email {sent_message_id} in database")
                    
            except Exception as e:
                logger.error(f"❌ Error storing sent email {sent_message_id}: {str(e)}")
                # Don't fail the entire operation for this
            
            # Success - no response data needed
            return {}
            
        except Exception as e:
            logger.error(f"❌ Error sending reply for user {self.internal_user_id}: {str(e)}")
            return {"error": f"Failed to send reply: {str(e)}"}
