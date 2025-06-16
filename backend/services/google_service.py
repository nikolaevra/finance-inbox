import os
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from dotenv import load_dotenv

load_dotenv()

class GoogleService:
    def __init__(self):
        self.client_id = os.environ["GOOGLE_CLIENT_ID"]
        self.client_secret = os.environ["GOOGLE_CLIENT_SECRET"]
        self.redirect_uri = os.environ["GOOGLE_REDIRECT_URI"]
        self.scopes = [
            "https://www.googleapis.com/auth/gmail.readonly",
            "openid", "email", "profile"
        ]
        # For demo only; use a database in production!
        self.tokens = {}

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
            include_granted_scopes='true'
        )
        # Save state in session if you use one
        return authorization_url

    def handle_oauth_callback(self, code: str) -> dict:
        """Handle OAuth callback and store tokens"""
        if not code:
            return {"error": "No authorization code provided"}

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
            flow.fetch_token(code=code)
            credentials = flow.credentials
            
            # Store the credentials for the user (in memory for demo)
            self.tokens["access_token"] = credentials.token
            self.tokens["refresh_token"] = credentials.refresh_token
            
            return {"message": "Authentication complete. Tokens received."}
        except Exception as e:
            return {"error": f"Authentication failed: {str(e)}"}

    def fetch_gmail_emails(self) -> list:
        """Fetch Gmail emails using stored credentials"""
        if not self.tokens or not self.tokens.get("access_token"):
            return []

        try:
            # Build credentials object
            creds_obj = Credentials(
                self.tokens["access_token"],
                refresh_token=self.tokens["refresh_token"],
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.client_id,
                client_secret=self.client_secret,
            )
            
            # Build Gmail service
            service = build('gmail', 'v1', credentials=creds_obj)
            
            # Fetch messages
            result = service.users().messages().list(
                userId='me', 
                maxResults=10
            ).execute()
            
            messages = result.get('messages', [])
            emails = []
            
            for msg in messages:
                msg_data = service.users().messages().get(
                    userId='me', 
                    id=msg['id']
                ).execute()
                
                snippet = msg_data.get('snippet')
                emails.append({
                    'id': msg['id'],
                    'snippet': snippet,
                })
            
            return emails
            
        except Exception as e:
            # Log the error in production
            print(f"Error fetching emails: {str(e)}")
            return []

    def get_tokens(self) -> dict:
        """Get stored tokens (for debugging/testing)"""
        return self.tokens

    def clear_tokens(self) -> dict:
        """Clear stored tokens"""
        self.tokens = {}
        return {"message": "Tokens cleared"}

    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        return bool(self.tokens and self.tokens.get("access_token"))
