from googleapiclient.discovery import build
from services.google_auth import TOKENS
from fastapi import APIRouter
import os

router = APIRouter()

@router.get("/emails")
def get_emails():
    emails = fetch_gmail_emails()
    return emails


def fetch_gmail_emails():
    creds = TOKENS  # Use user's stored credentials
    if not creds or not creds.get("access_token"):
        return []

    service = build('gmail', 'v1', credentials=None)
    # Instead, build credentials object with proper google.oauth2.credentials.Credentials class:
    from google.oauth2.credentials import Credentials
    creds_obj = Credentials(
        creds["access_token"],
        refresh_token=creds["refresh_token"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["GOOGLE_CLIENT_ID"],
        client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
    )
    service = build('gmail', 'v1', credentials=creds_obj)
    result = service.users().messages().list(userId='me', maxResults=10).execute()
    messages = result.get('messages', [])

    emails = []
    for msg in messages:
        msg_data = service.users().messages().get(userId='me', id=msg['id']).execute()
        snippet = msg_data.get('snippet')
        emails.append({
            'id': msg['id'],
            'snippet': snippet,
        })
    return emails
