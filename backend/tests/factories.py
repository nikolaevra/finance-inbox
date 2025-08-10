"""Factory classes for generating test data."""

import factory
from datetime import datetime, timedelta
from uuid import uuid4
from faker import Faker
from models import UserAuthData, EmailDetails, User, Connection, Email, OAuthToken, ConnectionProvider, ConnectionStatus

fake = Faker()

class UserAuthDataFactory(factory.Factory):
    class Meta:
        model = UserAuthData
    
    access_token = factory.LazyFunction(lambda: f"mock_access_token_{fake.uuid4()}")
    refresh_token = factory.LazyFunction(lambda: f"mock_refresh_token_{fake.uuid4()}")
    token_type = "Bearer"
    expires_at = factory.LazyFunction(lambda: int((datetime.now() + timedelta(hours=1)).timestamp()))
    user = factory.LazyFunction(lambda: {
        "id": str(uuid4()),
        "email": fake.email(),
        "user_metadata": {
            "full_name": fake.name()
        }
    })

class EmailDetailsFactory(factory.Factory):
    class Meta:
        model = EmailDetails
    
    id = factory.LazyFunction(lambda: fake.uuid4())
    thread_id = factory.LazyFunction(lambda: fake.uuid4())
    subject = factory.LazyFunction(lambda: fake.sentence())
    from_email = factory.LazyFunction(lambda: fake.email())
    to_email = factory.LazyFunction(lambda: fake.email())
    date = factory.LazyFunction(lambda: fake.date_time().isoformat())
    snippet = factory.LazyFunction(lambda: fake.text(max_nb_chars=200))
    body = factory.LazyFunction(lambda: {
        "text": fake.text(),
        "html": f"<p>{fake.text()}</p>"
    })
    labels = factory.LazyFunction(lambda: ["INBOX", "UNREAD"])
    has_attachments = False
    size_estimate = factory.LazyFunction(lambda: fake.random_int(min=100, max=50000))
    cc_email = factory.LazyFunction(lambda: fake.email() if fake.boolean() else None)
    bcc_email = None

class UserFactory(factory.Factory):
    class Meta:
        model = User
    
    id = factory.LazyFunction(uuid4)
    supabase_user_id = factory.LazyFunction(lambda: str(uuid4()))
    email = factory.LazyFunction(lambda: fake.email())
    created_at = factory.LazyFunction(lambda: fake.date_time())
    business_id = factory.LazyFunction(uuid4)
    full_name = factory.LazyFunction(lambda: fake.name())
    avatar_url = factory.LazyFunction(lambda: fake.image_url())
    last_sign_in_at = factory.LazyFunction(lambda: fake.date_time())

class ConnectionFactory(factory.Factory):
    class Meta:
        model = Connection
    
    id = factory.LazyFunction(uuid4)
    user_id = factory.LazyFunction(uuid4)
    connection_provider = ConnectionProvider.GMAIL
    status = ConnectionStatus.CONNECTED
    oauth_token_id = factory.LazyFunction(uuid4)
    created_at = factory.LazyFunction(lambda: fake.date_time())
    updated_at = factory.LazyFunction(lambda: fake.date_time())
    last_sync_at = factory.LazyFunction(lambda: fake.date_time())
    metadata = factory.LazyFunction(lambda: {"provider_user_id": fake.uuid4()})

class OAuthTokenFactory(factory.Factory):
    class Meta:
        model = OAuthToken
    
    id = factory.LazyFunction(uuid4)
    provider = "google"
    access_token = factory.LazyFunction(lambda: f"ya29.{fake.uuid4()}")
    refresh_token = factory.LazyFunction(lambda: f"1//{fake.uuid4()}")
    token_type = "Bearer"
    expires_at = factory.LazyFunction(lambda: fake.date_time() + timedelta(hours=1))
    scope = "https://www.googleapis.com/auth/gmail.readonly"
    created_at = factory.LazyFunction(lambda: fake.date_time())
    updated_at = factory.LazyFunction(lambda: fake.date_time())

class EmailFactory(factory.Factory):
    class Meta:
        model = Email
    
    id = factory.LazyFunction(uuid4)
    user_id = factory.LazyFunction(uuid4)
    gmail_id = factory.LazyFunction(lambda: fake.uuid4())
    thread_id = factory.LazyFunction(lambda: fake.uuid4())
    subject = factory.LazyFunction(lambda: fake.sentence())
    from_email = factory.LazyFunction(lambda: fake.email())
    to_email = factory.LazyFunction(lambda: fake.email())
    cc_email = factory.LazyFunction(lambda: fake.email() if fake.boolean() else None)
    bcc_email = None
    reply_to = factory.LazyFunction(lambda: fake.email())
    date_sent = factory.LazyFunction(lambda: fake.date_time())
    snippet = factory.LazyFunction(lambda: fake.text(max_nb_chars=200))
    body_text = factory.LazyFunction(lambda: fake.text())
    body_html = factory.LazyFunction(lambda: f"<p>{fake.text()}</p>")
    labels = factory.LazyFunction(lambda: ["INBOX", "UNREAD"])
    has_attachments = False
    size_estimate = factory.LazyFunction(lambda: fake.random_int(min=100, max=50000))
    is_processed = False
    processed_at = None
    category = factory.LazyFunction(lambda: fake.random_element(elements=("financial", "business", "personal", "promotion")))
    category_confidence = factory.LazyFunction(lambda: fake.pyfloat(min_value=0.0, max_value=1.0))
    categorized_at = factory.LazyFunction(lambda: fake.date_time())
    category_prompt_version = "1.0"
    created_at = factory.LazyFunction(lambda: fake.date_time())
    updated_at = factory.LazyFunction(lambda: fake.date_time())

# Mock data generators for API responses
def generate_gmail_thread(email_count: int = 3):
    """Generate a mock Gmail thread with multiple emails."""
    thread_id = fake.uuid4()
    emails = []
    
    for i in range(email_count):
        email = EmailDetailsFactory().to_dict()
        email['thread_id'] = thread_id
        if i > 0:
            email['subject'] = f"Re: {emails[0]['subject']}"
        emails.append(email)
    
    return {
        "thread_id": thread_id,
        "emails": emails,
        "email_count": email_count,
        "participants": list(set([email['from'] for email in emails] + [email['to'] for email in emails])),
        "latest_date": max(email['date'] for email in emails),
        "has_unread": fake.boolean(),
        "subject": emails[0]['subject']
    }

def generate_slack_user_info():
    """Generate mock Slack user info response."""
    return {
        "user_id": fake.uuid4(),
        "user": fake.user_name(),
        "team_id": fake.uuid4(),
        "team": fake.company(),
        "url": f"https://{fake.domain_name()}.slack.com/"
    }

def generate_slack_channels(count: int = 5):
    """Generate mock Slack channels response."""
    channels = []
    for _ in range(count):
        channels.append({
            "id": fake.uuid4(),
            "name": fake.word(),
            "is_channel": True,
            "is_private": fake.boolean(),
            "is_member": fake.boolean(),
            "num_members": fake.random_int(min=1, max=50),
            "purpose": fake.sentence(),
            "topic": fake.sentence()
        })
    return channels

def generate_user_connections():
    """Generate mock user connections."""
    return [
        {
            "id": str(uuid4()),
            "provider": "gmail",
            "status": "connected",
            "connected_at": fake.date_time().isoformat(),
            "last_sync_at": fake.date_time().isoformat(),
            "metadata": {
                "email": fake.email()
            }
        },
        {
            "id": str(uuid4()),
            "provider": "slack",
            "status": "connected",
            "connected_at": fake.date_time().isoformat(),
            "last_sync_at": fake.date_time().isoformat(),
            "metadata": {
                "team_name": fake.company(),
                "user_name": fake.user_name()
            }
        }
    ]

def generate_prompt_config():
    """Generate mock prompt configuration."""
    return {
        "id": str(uuid4()),
        "user_id": str(uuid4()),
        "template": "Categorize this email: Subject: {subject}, From: {sender}, Content: {content}",
        "model": "gpt-3.5-turbo",
        "temperature": 0.1,
        "max_tokens": 200,
        "timeout": 10,
        "created_at": fake.date_time().isoformat(),
        "updated_at": fake.date_time().isoformat()
    } 