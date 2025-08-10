"""Pytest configuration and shared fixtures."""

import pytest
import asyncio
from datetime import datetime, timedelta
from uuid import uuid4
from fastapi.testclient import TestClient
from fastapi import Depends
from unittest.mock import Mock, patch
import os
import sys

# Add backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from main import app
from models import UserAuthData
from services.auth_service import get_current_user_profile

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def client():
    """Create a FastAPI test client with mocked authentication."""
    # Override the dependency before creating the test client
    app.dependency_overrides[get_current_user_profile] = mock_get_current_user_profile
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Clean up the override after the test
    app.dependency_overrides.clear()

@pytest.fixture
def mock_user_profile():
    """Mock user profile for testing authenticated endpoints."""
    # Use the same consistent UUIDs as mock_get_current_user_profile
    return {
        "id": "12345678-1234-1234-1234-123456789012",
        "user_id": "12345678-1234-1234-1234-123456789012",
        "email": "test@example.com",
        "supabase_user_id": "87654321-4321-4321-4321-210987654321",
        "full_name": "Test User",
        "created_at": datetime.now().isoformat()
    }

@pytest.fixture
def client_with_user(mock_user_profile):
    """Create a FastAPI test client with a specific user profile."""
    def custom_get_current_user_profile():
        return mock_user_profile
    
    # Override the dependency with the custom user profile
    app.dependency_overrides[get_current_user_profile] = custom_get_current_user_profile
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Clean up the override after the test
    app.dependency_overrides.clear()

@pytest.fixture
def unauthenticated_client():
    """Create a FastAPI test client without authentication."""
    # Don't override the dependency - let it fail naturally
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture
def mock_user_auth_data():
    """Mock user authentication data."""
    return UserAuthData(
        access_token="mock_access_token",
        refresh_token="mock_refresh_token",
        token_type="Bearer",
        expires_at=int((datetime.now() + timedelta(hours=1)).timestamp()),
        user={
            "id": str(uuid4()),
            "email": "test@example.com",
            "user_metadata": {
                "full_name": "Test User"
            }
        }
    )

@pytest.fixture
def mock_google_service():
    """Mock Google service."""
    with patch('services.google_service.GoogleService') as mock:
        mock_instance = Mock()
        mock.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_slack_service():
    """Mock Slack service."""
    with patch('services.slack_service.SlackService') as mock:
        mock_instance = Mock()
        mock.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_auth_service():
    """Mock authentication service."""
    with patch('apis.auth.auth_service') as mock:
        yield mock

@pytest.fixture
def mock_user_prompt_service():
    """Mock user prompt service."""
    with patch('services.user_prompt_service.user_prompt_service') as mock:
        yield mock

@pytest.fixture
def mock_connections_service():
    """Mock connections service."""
    with patch('services.connections_service.connections_service') as mock:
        yield mock

@pytest.fixture
def mock_token_manager():
    """Mock token manager."""
    with patch('services.token_manager.token_manager') as mock:
        yield mock

def mock_get_current_user_profile():
    """Mock function to replace get_current_user_profile dependency."""
    # Use consistent UUIDs for testing
    return {
        "id": "12345678-1234-1234-1234-123456789012",
        "user_id": "12345678-1234-1234-1234-123456789012",
        "email": "test@example.com",
        "supabase_user_id": "87654321-4321-4321-4321-210987654321",
        "full_name": "Test User",
        "created_at": datetime.now().isoformat()
    }

@pytest.fixture(autouse=True)
def mock_environment_variables():
    """Mock environment variables for testing."""
    with patch.dict(os.environ, {
        'FRONTEND_URL': 'http://localhost:5173',
        'SUPABASE_URL': 'http://localhost:54321',
        'SUPABASE_ANON_KEY': 'mock_anon_key',
        'SUPABASE_SERVICE_ROLE_KEY': 'mock_service_role_key',
        'GOOGLE_CLIENT_ID': 'mock_google_client_id',
        'GOOGLE_CLIENT_SECRET': 'mock_google_client_secret',
        'SLACK_CLIENT_ID': 'mock_slack_client_id',
        'SLACK_CLIENT_SECRET': 'mock_slack_client_secret',
        'OPENAI_API_KEY': 'mock_openai_api_key'
    }):
        yield

@pytest.fixture(autouse=True)
def mock_email_polling_service():
    """Mock email polling service to prevent real background tasks during tests."""
    with patch('main.email_polling_service') as mock_service:
        # Create a proper async mock coroutine
        async def mock_start_polling():
            return None
        
        mock_service.start_polling_all_users = Mock(return_value=mock_start_polling())
        mock_service.stop = Mock(return_value=None)
        yield mock_service 