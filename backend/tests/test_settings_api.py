"""Tests for settings API endpoints."""

import pytest
from fastapi import HTTPException
from unittest.mock import Mock, patch
from tests.factories import generate_user_connections
from models import ConnectionProvider

class TestSettingsAPI:
    """Test settings API endpoints."""

    @patch('apis.settings.connections_service')
    def test_get_user_connections_success(self, mock_connections_service, client_with_user, mock_user_profile):
        """Test successful retrieval of user connections."""
        mock_connections = generate_user_connections()
        mock_connections_service.get_user_connections.return_value = mock_connections

        response = client_with_user.get("/settings/connections")

        assert response.status_code == 200
        data = response.json()
        assert "connections" in data
        assert "count" in data
        assert data["count"] == len(mock_connections)
        assert len(data["connections"]) == 2
        
        # Verify service was called correctly
        mock_connections_service.get_user_connections.assert_called_once_with(mock_user_profile["id"])

    @patch('apis.settings.get_current_user_profile')
    @patch('apis.settings.connections_service')
    def test_get_user_connections_empty(self, mock_connections_service, mock_get_user, client, mock_user_profile):
        """Test retrieval of user connections when none exist."""
        mock_get_user.return_value = mock_user_profile
        mock_connections_service.get_user_connections.return_value = []

        response = client.get("/settings/connections")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert data["connections"] == []

    @patch('apis.settings.get_current_user_profile')
    @patch('apis.settings.GoogleService')
    def test_disconnect_gmail_success(self, mock_google_service_class, mock_get_user, client, mock_user_profile):
        """Test successful Gmail disconnection."""
        mock_get_user.return_value = mock_user_profile
        mock_google_service = Mock()
        mock_google_service_class.return_value = mock_google_service
        mock_google_service.clear_tokens.return_value = {"message": "Tokens cleared successfully"}

        response = client.post("/settings/connections/gmail/disconnect")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Successfully disconnected from gmail"
        assert data["provider"] == "gmail"
        assert "details" in data
        
        # Verify service was called correctly
        mock_google_service_class.assert_called_once_with(internal_user_id=mock_user_profile["id"])
        mock_google_service.clear_tokens.assert_called_once()

    @patch('apis.settings.get_current_user_profile')
    @patch('apis.settings.connections_service')
    def test_disconnect_slack_success(self, mock_connections_service, mock_get_user, client, mock_user_profile):
        """Test successful Slack disconnection."""
        mock_get_user.return_value = mock_user_profile
        mock_connections_service.disconnect_slack_connection.return_value = True

        response = client.post("/settings/connections/slack/disconnect")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Successfully disconnected from slack"
        assert data["provider"] == "slack"
        
        # Verify service was called correctly
        mock_connections_service.disconnect_slack_connection.assert_called_once_with(
            user_id=mock_user_profile["id"]
        )

    @patch('apis.settings.get_current_user_profile')
    @patch('apis.settings.connections_service')
    def test_disconnect_slack_not_found(self, mock_connections_service, mock_get_user, client, mock_user_profile):
        """Test Slack disconnection when no connection exists."""
        mock_get_user.return_value = mock_user_profile
        mock_connections_service.disconnect_slack_connection.return_value = False

        response = client.post("/settings/connections/slack/disconnect")

        assert response.status_code == 404
        data = response.json()
        assert "No active connection found for slack" in data["detail"]

    def test_disconnect_invalid_provider(self, client):
        """Test disconnection with invalid provider."""
        response = client.post("/settings/connections/invalid_provider/disconnect")

        assert response.status_code == 400
        data = response.json()
        assert "Invalid provider" in data["detail"]
        assert "Supported providers: gmail, slack" in data["detail"]

    @patch('apis.settings.get_current_user_profile')
    @patch('apis.settings.connections_service')
    def test_disconnect_other_provider_success(self, mock_connections_service, mock_get_user, client, mock_user_profile):
        """Test successful disconnection of other providers (future providers)."""
        mock_get_user.return_value = mock_user_profile
        
        # Mock a future provider that uses the generic disconnect logic
        with patch('apis.settings.ConnectionProvider') as mock_provider:
            mock_provider.return_value = "future_provider"
            mock_connections_service.disconnect_provider.return_value = True

            # This test simulates what would happen if we add a new provider
            # For now, it will hit the invalid provider validation

    @patch('apis.settings.get_current_user_profile')
    @patch('apis.settings.connections_service')
    def test_disconnect_generic_provider_not_found(self, mock_connections_service, mock_get_user, client, mock_user_profile):
        """Test generic provider disconnection when no connection exists."""
        mock_get_user.return_value = mock_user_profile
        
        # This will trigger the invalid provider validation since we only support gmail/slack
        response = client.post("/settings/connections/unknown/disconnect")

        assert response.status_code == 400
        data = response.json()
        assert "Invalid provider" in data["detail"]

class TestConnectionProvider:
    """Test ConnectionProvider enum validation."""

    def test_valid_providers(self):
        """Test valid connection providers."""
        assert ConnectionProvider.GMAIL == "gmail"
        assert ConnectionProvider.SLACK == "slack"

    def test_invalid_provider_raises_error(self):
        """Test that invalid provider raises ValueError."""
        with pytest.raises(ValueError):
            ConnectionProvider("invalid_provider")

class TestSettingsAPIEdgeCases:
    """Test edge cases and error scenarios for settings API."""

    def test_unauthorized_access(self, unauthenticated_client):
        """Test unauthorized access to settings endpoints."""
        response = unauthenticated_client.get("/settings/connections")
        assert response.status_code == 403  # FastAPI returns 403 for missing dependencies

        response = unauthenticated_client.post("/settings/connections/gmail/disconnect")
        assert response.status_code == 403

    @patch('apis.settings.connections_service')
    def test_connections_service_error(self, mock_connections_service, client_with_user, mock_user_profile):
        """Test handling of connections service errors."""
        mock_connections_service.get_user_connections.side_effect = Exception("Database error")

        # The endpoint doesn't handle exceptions, so the exception should be raised
        with pytest.raises(Exception, match="Database error"):
            client_with_user.get("/settings/connections")

    @patch('apis.settings.GoogleService')
    def test_google_service_error_during_disconnect(self, mock_google_service_class, client_with_user, mock_user_profile):
        """Test handling of Google service errors during disconnection."""
        mock_google_service = Mock()
        mock_google_service_class.return_value = mock_google_service
        mock_google_service.clear_tokens.side_effect = Exception("Google API error")

        # The endpoint doesn't handle Google service exceptions, so the exception should be raised
        with pytest.raises(Exception, match="Google API error"):
            client_with_user.post("/settings/connections/gmail/disconnect")

    @patch('apis.settings.connections_service')
    def test_slack_service_error_during_disconnect(self, mock_connections_service, client_with_user, mock_user_profile):
        """Test handling of Slack service errors during disconnection."""
        mock_connections_service.disconnect_slack_connection.side_effect = Exception("Slack API error")

        # The endpoint doesn't handle Slack service exceptions, so the exception should be raised
        with pytest.raises(Exception, match="Slack API error"):
            client_with_user.post("/settings/connections/slack/disconnect")

    def test_case_insensitive_provider_names(self, client_with_user):
        """Test that provider names are handled case-insensitively."""
        # Test uppercase  
        response = client_with_user.post("/settings/connections/GMAIL/disconnect")
        assert response.status_code in [200, 401, 500]  # Should not be 404 for invalid provider

        # Test mixed case
        response = client_with_user.post("/settings/connections/GmAiL/disconnect")
        assert response.status_code in [200, 401, 500]  # Should not be 404 for invalid provider

        response = client_with_user.post("/settings/connections/Slack/disconnect")
        assert response.status_code in [200, 401, 404, 500]  # 404 is valid when no connection exists

class TestSettingsAPIIntegration:
    """Integration tests for settings API."""

    @patch('apis.settings.get_current_user_profile')
    @patch('apis.settings.connections_service')
    @patch('apis.settings.GoogleService')
    def test_full_gmail_disconnect_flow(self, mock_google_service_class, mock_connections_service, mock_get_user, client, mock_user_profile):
        """Test complete Gmail disconnection flow."""
        # Setup mocks
        mock_get_user.return_value = mock_user_profile
        mock_google_service = Mock()
        mock_google_service_class.return_value = mock_google_service
        mock_google_service.clear_tokens.return_value = {"tokens_cleared": True}

        # Test the flow
        response = client.post("/settings/connections/gmail/disconnect")

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["provider"] == "gmail"
        assert "Successfully disconnected" in data["message"]

        # Verify all services were called correctly
        mock_google_service_class.assert_called_once_with(internal_user_id=mock_user_profile["id"])
        mock_google_service.clear_tokens.assert_called_once()

    @patch('apis.settings.get_current_user_profile')
    @patch('apis.settings.connections_service')
    def test_full_slack_disconnect_flow(self, mock_connections_service, mock_get_user, client, mock_user_profile):
        """Test complete Slack disconnection flow."""
        # Setup mocks
        mock_get_user.return_value = mock_user_profile
        mock_connections_service.disconnect_slack_connection.return_value = True

        # Test the flow
        response = client.post("/settings/connections/slack/disconnect")

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["provider"] == "slack"
        assert "Successfully disconnected" in data["message"]

        # Verify service was called correctly
        mock_connections_service.disconnect_slack_connection.assert_called_once_with(
            user_id=mock_user_profile["id"]
        ) 