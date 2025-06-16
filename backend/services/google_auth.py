import os
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from dotenv import load_dotenv
from google_auth_oauthlib.flow import Flow

load_dotenv()

router = APIRouter()
CLIENT_ID = os.environ["GOOGLE_CLIENT_ID"]
CLIENT_SECRET = os.environ["GOOGLE_CLIENT_SECRET"]
REDIRECT_URI = os.environ["GOOGLE_REDIRECT_URI"]

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "openid", "email", "profile"
]

# Step 1: Send user to Google login
@router.get("/login")
def login():
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )
    authorization_url, state = flow.authorization_url(access_type='offline', include_granted_scopes='true')
    # Save state in session if you use one
    return RedirectResponse(authorization_url)

# Step 2: Handle Google OAuth callback
TOKENS = {}  # For demo only; use a database in production!

@router.get("/oauth2callback")
def oauth2callback(request: Request):
    code = request.query_params.get("code")
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )
    flow.fetch_token(code=code)
    credentials = flow.credentials
    # Store the credentials for the user (in memory for demo)
    TOKENS["access_token"] = credentials.token
    TOKENS["refresh_token"] = credentials.refresh_token
    return {"message": "Authentication complete. Tokens received."}
