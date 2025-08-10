"""Tests for connection API endpoints (Gmail OAuth and Slack OAuth)."""

import pytest
from fastapi import HTTPException
from unittest.mock import Mock, patch
from tests.factories import generate_slack_user_info, generate_slack_channels

class TestGmailOAuthAPI:
    """Test Gmail OAuth API endpoints."""

    @patch('apis.connect_gmail.GoogleService')
    def test_gmail_login_success(self, mock_google_service_class, client_with_user, mock_user_profile):
        """Test successful Gmail OAuth URL generation."""
        mock_google_service = Mock()
        mock_google_service_class.return_value = mock_google_service
        mock_google_service.get_authorization_url.return_value = "https://accounts.google.com/oauth/authorize?..."

        response = client_with_user.get("/google-auth/")

        assert response.status_code == 200
        data = response.json()
        assert "authorization_url" in data
        assert "message" in data
        assert data["authorization_url"] == "https://accounts.google.com/oauth/authorize?..."
        assert "Use this URL to redirect user to Google OAuth" in data["message"]
        
        # Verify service was called correctly
        mock_google_service_class.assert_called_once_with(internal_user_id=mock_user_profile["id"])
        mock_google_service.get_authorization_url.assert_called_once_with(state=mock_user_profile["id"])

    @patch('apis.connect_gmail.GoogleService')
    def test_gmail_oauth_callback_success(self, mock_google_service_class, unauthenticated_client):
        """Test successful Gmail OAuth callback."""
        mock_google_service = Mock()
        mock_google_service_class.return_value = mock_google_service
        mock_google_service.handle_oauth_callback.return_value = {"success": True, "tokens_stored": True}

        response = unauthenticated_client.get("/google-auth/callback?code=test_code&state=test_user_id", follow_redirects=False)

        assert response.status_code in [302, 307]  # Redirect response (302 Found or 307 Temporary Redirect)
        assert "success=gmail_connected" in response.headers["location"]
        
        # Verify service was called correctly
        mock_google_service_class.assert_called_once_with(internal_user_id="test_user_id")
        mock_google_service.handle_oauth_callback.assert_called_once_with("test_code")

    def test_gmail_oauth_callback_no_code(self, unauthenticated_client):
        """Test Gmail OAuth callback without authorization code."""
        response = unauthenticated_client.get("/google-auth/callback?state=test_user_id", follow_redirects=False)

        assert response.status_code in [302, 307]
        assert "error=no_code" in response.headers["location"]

    def test_gmail_oauth_callback_no_code(self, unauthenticated_client):
        """Test Gmail OAuth callback without state parameter."""
        response = unauthenticated_client.get("/google-auth/callback?code=test_code", follow_redirects=False)

        assert response.status_code in [302, 307]
        assert "error=no_state" in response.headers["location"]

    @patch('apis.connect_gmail.GoogleService')
    def test_gmail_oauth_callback_service_error(self, mock_google_service_class, unauthenticated_client):
        """Test Gmail OAuth callback with service error."""
        mock_google_service = Mock()
        mock_google_service_class.return_value = mock_google_service
        mock_google_service.handle_oauth_callback.return_value = {"error": "Invalid code"}

        response = unauthenticated_client.get("/google-auth/callback?code=invalid_code&state=test_user_id", follow_redirects=False)

        assert response.status_code in [302, 307]
        assert "error=Invalid%20code" in response.headers["location"]

    @patch('apis.connect_gmail.GoogleService')
    def test_gmail_oauth_callback_exception(self, mock_google_service_class, unauthenticated_client):
        """Test Gmail OAuth callback with exception."""
        mock_google_service = Mock()
        mock_google_service_class.return_value = mock_google_service
        mock_google_service.handle_oauth_callback.side_effect = Exception("Service unavailable")

        response = unauthenticated_client.get("/google-auth/callback?code=test_code&state=test_user_id", follow_redirects=False)

        assert response.status_code in [302, 307]
        assert "error=callback_failed" in response.headers["location"]
    @patch('apis.connect_gmail.GoogleService')
    def test_gmail_auth_status(self, mock_google_service_class, client_with_user, mock_user_profile):
        """Test Gmail authentication status check."""
        mock_google_service = Mock()
        mock_google_service_class.return_value = mock_google_service
        mock_google_service.get_token_info.return_value = {
            "authenticated": True,
            "expires_at": "2024-12-31T23:59:59Z"
        }

        response = client_with_user.get("/google-auth/status")

        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] is True
        assert "expires_at" in data
        
        mock_google_service.get_token_info.assert_called_once()
    @patch('apis.connect_gmail.GoogleService')
    def test_gmail_logout(self, mock_google_service_class, client_with_user, mock_user_profile):
        """Test Gmail logout (clear tokens)."""
        mock_google_service = Mock()
        mock_google_service_class.return_value = mock_google_service
        mock_google_service.clear_tokens.return_value = {"message": "Tokens cleared successfully"}

        response = client_with_user.post("/google-auth/logout")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Tokens cleared successfully"
        
        mock_google_service.clear_tokens.assert_called_once()
    @patch('apis.connect_gmail.GoogleService')
    def test_gmail_force_consent(self, mock_google_service_class, client_with_user, mock_user_profile):
        """Test Gmail force consent URL generation."""
        mock_google_service = Mock()
        mock_google_service_class.return_value = mock_google_service
        mock_google_service.get_authorization_url.return_value = "https://accounts.google.com/oauth/authorize?prompt=consent..."

        response = client_with_user.get("/google-auth/force-consent")

        assert response.status_code == 200
        data = response.json()
        assert "authorization_url" in data
        assert "message" in data
        assert "force the consent screen" in data["message"]
        
        mock_google_service.get_authorization_url.assert_called_once()

class TestSlackOAuthAPI:
    """Test Slack OAuth API endpoints."""
    @patch('apis.connect_slack.SlackService')
    def test_slack_login_success(self, mock_slack_service_class, client_with_user, mock_user_profile):
        """Test successful Slack OAuth URL generation."""
        mock_slack_service = Mock()
        mock_slack_service_class.return_value = mock_slack_service
        mock_slack_service.get_authorization_url.return_value = "https://slack.com/oauth/authorize?..."

        response = client_with_user.get("/slack-auth/")

        assert response.status_code == 200
        data = response.json()
        assert "authorization_url" in data
        assert "message" in data
        assert data["authorization_url"] == "https://slack.com/oauth/authorize?..."
        assert "Use this URL to redirect user to Slack OAuth" in data["message"]
        
        # Verify service was called correctly
        mock_slack_service_class.assert_called_once_with(internal_user_id=mock_user_profile["id"])
        mock_slack_service.get_authorization_url.assert_called_once_with(state=mock_user_profile["id"])

    @patch('apis.connect_slack.SlackService')
    def test_slack_oauth_callback_success(self, mock_slack_service_class, unauthenticated_client):
        """Test successful Slack OAuth callback."""
        mock_slack_service = Mock()
        mock_slack_service_class.return_value = mock_slack_service
        mock_slack_service.handle_oauth_callback.return_value = {"success": True, "tokens_stored": True}

        response = unauthenticated_client.get("/slack-auth/callback?code=test_code&state=test_user_id", follow_redirects=False)

        assert response.status_code in [302, 307]  # Redirect response
        assert "success=slack_connected" in response.headers["location"]
        
        # Verify service was called correctly
        mock_slack_service_class.assert_called_once_with(internal_user_id="test_user_id")
        mock_slack_service.handle_oauth_callback.assert_called_once_with("test_code")

    def test_gmail_oauth_callback_no_code(self, unauthenticated_client):
        """Test Slack OAuth callback without authorization code."""
        response = unauthenticated_client.get("/slack-auth/callback?state=test_user_id", follow_redirects=False)

        assert response.status_code in [302, 307]
        assert "error=no_code" in response.headers["location"]

    def test_gmail_oauth_callback_no_code(self, unauthenticated_client):
        """Test Slack OAuth callback without state parameter."""
        response = unauthenticated_client.get("/slack-auth/callback?code=test_code", follow_redirects=False)

        assert response.status_code in [302, 307]
        assert "error=no_state" in response.headers["location"]

    @patch('apis.connect_slack.SlackService')
    def test_slack_oauth_callback_service_error(self, mock_slack_service_class, unauthenticated_client):
        """Test Slack OAuth callback with service error."""
        mock_slack_service = Mock()
        mock_slack_service_class.return_value = mock_slack_service
        mock_slack_service.handle_oauth_callback.return_value = {"error": "Invalid code"}

        response = unauthenticated_client.get("/slack-auth/callback?code=invalid_code&state=test_user_id", follow_redirects=False)

        assert response.status_code in [302, 307]
        assert "error=Invalid%20code" in response.headers["location"]

    @patch('apis.connect_slack.SlackService')
    def test_slack_oauth_callback_exception(self, mock_slack_service_class, unauthenticated_client):
        """Test Slack OAuth callback with exception."""
        mock_slack_service = Mock()
        mock_slack_service_class.return_value = mock_slack_service
        mock_slack_service.handle_oauth_callback.side_effect = Exception("Service unavailable")

        response = unauthenticated_client.get("/slack-auth/callback?code=test_code&state=test_user_id", follow_redirects=False)

        assert response.status_code in [302, 307]
        assert "error=callback_failed" in response.headers["location"]
    @patch('apis.connect_slack.SlackService')
    def test_slack_auth_status_connected(self, mock_slack_service_class, client_with_user, mock_user_profile):
        """Test Slack authentication status when connected."""
        mock_slack_service = Mock()
        mock_slack_service_class.return_value = mock_slack_service
        mock_slack_service.get_valid_token.return_value = "valid_token"
        mock_slack_service.test_connection.return_value = True

        response = client_with_user.get("/slack-auth/status")

        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] is True
        assert data["connection_status"] == "connected"
    @patch('apis.connect_slack.SlackService')
    def test_slack_auth_status_disconnected(self, mock_slack_service_class, client_with_user, mock_user_profile):
        """Test Slack authentication status when disconnected."""
        mock_slack_service = Mock()
        mock_slack_service_class.return_value = mock_slack_service
        mock_slack_service.get_valid_token.return_value = None

        response = client_with_user.get("/slack-auth/status")

        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] is False
        assert data["connection_status"] == "disconnected"
    @patch('apis.connect_slack.SlackService')
    def test_slack_auth_status_connection_error(self, mock_slack_service_class, client_with_user, mock_user_profile):
        """Test Slack authentication status with connection error."""
        mock_slack_service = Mock()
        mock_slack_service_class.return_value = mock_slack_service
        mock_slack_service.get_valid_token.return_value = "valid_token"
        mock_slack_service.test_connection.return_value = False

        response = client_with_user.get("/slack-auth/status")

        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] is True
        assert data["connection_status"] == "error"
    @patch('apis.connect_slack.SlackService')
    def test_slack_auth_status_exception(self, mock_slack_service_class, client_with_user, mock_user_profile):
        """Test Slack authentication status with service exception."""
        mock_slack_service = Mock()
        mock_slack_service_class.return_value = mock_slack_service
        mock_slack_service.get_valid_token.side_effect = Exception("Service error")

        response = client_with_user.get("/slack-auth/status")

        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] is False
        assert data["connection_status"] == "error"
        assert "error" in data

    @patch('services.connections_service.connections_service')
    def test_slack_disconnect_success(self, mock_connections_service, client_with_user, mock_user_profile):
        """Test successful Slack disconnection."""
        mock_connections_service.disconnect_provider.return_value = True

        response = client_with_user.delete("/slack-auth/disconnect")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Slack disconnected successfully"

    @patch('services.connections_service.connections_service')
    def test_slack_disconnect_failure(self, mock_connections_service, client_with_user, mock_user_profile):
        """Test Slack disconnection failure."""
        mock_connections_service.disconnect_provider.return_value = False

        response = client_with_user.delete("/slack-auth/disconnect")

        assert response.status_code == 200
        data = response.json()
        assert data["error"] == "Failed to disconnect Slack"

    @patch('services.connections_service.connections_service')
    def test_slack_disconnect_exception(self, mock_connections_service, client_with_user, mock_user_profile):
        """Test Slack disconnection with exception."""
        mock_connections_service.disconnect_provider.side_effect = Exception("Database error")

        response = client_with_user.delete("/slack-auth/disconnect")

        assert response.status_code == 500
        data = response.json()
        assert data["detail"] == "Failed to disconnect Slack"

class TestSlackAPI:
    """Test Slack API endpoints."""
    @patch('apis.slack_api.token_manager')
    @patch('apis.slack_api.requests')
    def test_get_slack_user_info_success(self, mock_requests, mock_token_manager, client_with_user, mock_user_profile):
        """Test successful Slack user info retrieval."""
        mock_token_manager.get_valid_token.return_value = "valid_slack_token"
        
        # Mock Slack API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "ok": True,
            **generate_slack_user_info()
        }
        mock_requests.get.return_value = mock_response

        response = client_with_user.get("/slack-api/user-info")

        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert "user" in data
        assert "team_id" in data
        assert "team" in data
        assert "url" in data

        # Verify token manager was called
        mock_token_manager.get_valid_token.assert_called_once()
    @patch('apis.slack_api.token_manager')
    def test_get_slack_user_info_no_token(self, mock_token_manager, client_with_user, mock_user_profile):
        """Test Slack user info retrieval without valid token."""
        mock_token_manager.get_valid_token.return_value = None

        response = client_with_user.get("/slack-api/user-info")

        assert response.status_code == 401
        data = response.json()
        assert "No valid Slack token available" in data["detail"]
    @patch('apis.slack_api.token_manager')
    @patch('apis.slack_api.requests')
    def test_get_slack_user_info_api_error(self, mock_requests, mock_token_manager, client_with_user, mock_user_profile):
        """Test Slack user info retrieval with API error."""
        mock_token_manager.get_valid_token.return_value = "valid_slack_token"
        
        # Mock Slack API error response
        mock_response = Mock()
        mock_response.json.return_value = {
            "ok": False,
            "error": "invalid_auth"
        }
        mock_requests.get.return_value = mock_response

        response = client_with_user.get("/slack-api/user-info")

        assert response.status_code == 400
        data = response.json()
        assert "Slack API error: invalid_auth" in data["detail"]
    @patch('apis.slack_api.token_manager')
    @patch('apis.slack_api.requests')
    def test_get_slack_channels_success(self, mock_requests, mock_token_manager, client_with_user, mock_user_profile):
        """Test successful Slack channels retrieval."""
        mock_token_manager.get_valid_token.return_value = "valid_slack_token"
        
        # Mock Slack API response - fix structure to match Slack API format
        mock_channels = []
        for i in range(3):
            mock_channels.append({
                "id": f"C{i}234567890",
                "name": f"test-channel-{i}",
                "is_channel": True,
                "is_private": False,
                "is_member": True,
                "num_members": 10 + i,
                "purpose": {"value": f"Purpose for channel {i}"},
                "topic": {"value": f"Topic for channel {i}"}
            })
        mock_response = Mock()
        mock_response.json.return_value = {
            "ok": True,
            "channels": mock_channels
        }
        mock_response.raise_for_status.return_value = None
        mock_requests.get.return_value = mock_response

        response = client_with_user.get("/slack-api/channels")

        assert response.status_code == 200
        data = response.json()
        assert "channels" in data
        assert "count" in data
        assert data["count"] == 3
        assert len(data["channels"]) == 3
    @patch('apis.slack_api.token_manager')
    def test_get_slack_channels_no_token(self, mock_token_manager, client_with_user, mock_user_profile):
        """Test Slack channels retrieval without valid token."""
        mock_token_manager.get_valid_token.return_value = None

        response = client_with_user.get("/slack-api/channels")

        assert response.status_code == 401
        data = response.json()
        assert "No valid Slack token available" in data["detail"]
    @patch('apis.slack_api.token_manager')
    def test_test_slack_connection_success(self, mock_token_manager, client_with_user, mock_user_profile):
        """Test successful Slack connection test."""
        mock_token_manager.test_token_validity.return_value = True

        response = client_with_user.get("/slack-api/test-connection")

        assert response.status_code == 200
        data = response.json()
        assert data["connected"] is True
        assert data["provider"] == "slack"
        assert "Connection is working" in data["message"]
    @patch('apis.slack_api.token_manager')
    def test_test_slack_connection_failure(self, mock_token_manager, client_with_user, mock_user_profile):
        """Test Slack connection test failure."""
        mock_token_manager.test_token_validity.return_value = False

        response = client_with_user.get("/slack-api/test-connection")

        assert response.status_code == 200
        data = response.json()
        assert data["connected"] is False
        assert data["provider"] == "slack"
        assert "Connection failed or needs refresh" in data["message"]
    @patch('apis.slack_api.token_manager')
    def test_test_slack_connection_exception(self, mock_token_manager, client_with_user, mock_user_profile):
        """Test Slack connection test with exception."""
        mock_token_manager.test_token_validity.side_effect = Exception("Service error")

        response = client_with_user.get("/slack-api/test-connection")

        assert response.status_code == 200
        data = response.json()
        assert data["connected"] is False
        assert data["provider"] == "slack"
        assert "Connection test failed" in data["message"]

class TestConnectionAPIEdgeCases:
    """Test edge cases and error scenarios for connection APIs."""
    def test_gmail_unauthorized_access(self, unauthenticated_client):
        """Test unauthorized access to Gmail endpoints."""
        response = unauthenticated_client.get("/google-auth/")
        assert response.status_code == 403  # FastAPI returns 403 for missing dependencies

        response = unauthenticated_client.get("/google-auth/status")
        assert response.status_code == 403

        response = unauthenticated_client.post("/google-auth/logout")
        assert response.status_code == 403
    def test_slack_unauthorized_access(self, unauthenticated_client):
        """Test unauthorized access to Slack endpoints."""
        response = unauthenticated_client.get("/slack-auth/")
        assert response.status_code == 403

        response = unauthenticated_client.get("/slack-auth/status")
        assert response.status_code == 403

        response = unauthenticated_client.delete("/slack-auth/disconnect")
        assert response.status_code == 403
    def test_slack_api_unauthorized_access(self, unauthenticated_client):
        """Test unauthorized access to Slack API endpoints."""
        response = unauthenticated_client.get("/slack-api/user-info")
        assert response.status_code == 403

        response = unauthenticated_client.get("/slack-api/channels")
        assert response.status_code == 403

        response = unauthenticated_client.get("/slack-api/test-connection")
        assert response.status_code == 403 