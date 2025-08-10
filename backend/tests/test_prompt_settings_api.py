"""Tests for prompt settings API endpoints."""

import pytest
from fastapi import HTTPException
from unittest.mock import Mock, patch
from tests.factories import generate_prompt_config

class TestPromptSettingsAPI:
    """Test prompt settings API endpoints."""

    @patch('apis.prompt_settings.get_current_user_profile')
    @patch('apis.prompt_settings.user_prompt_service')
    def test_get_user_prompt_success(self, mock_user_prompt_service, mock_get_user, client, mock_user_profile):
        """Test successful retrieval of user prompt configuration."""
        mock_get_user.return_value = mock_user_profile
        mock_prompt_config = generate_prompt_config()
        mock_user_prompt_service.get_user_prompt_config.return_value = mock_prompt_config

        response = client.get("/settings/prompt")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "prompt" in data
        assert data["prompt"]["template"] == mock_prompt_config["template"]
        assert data["prompt"]["model"] == mock_prompt_config["model"]
        
        # Verify service was called correctly
        mock_user_prompt_service.get_user_prompt_config.assert_called_once_with(mock_user_profile["user_id"])

    @patch('apis.prompt_settings.get_current_user_profile')
    @patch('apis.prompt_settings.user_prompt_service')
    def test_get_user_prompt_service_error(self, mock_user_prompt_service, mock_get_user, client, mock_user_profile):
        """Test get user prompt with service error."""
        mock_get_user.return_value = mock_user_profile
        mock_user_prompt_service.get_user_prompt_config.side_effect = Exception("Database error")

        response = client.get("/settings/prompt")

        assert response.status_code == 500
        data = response.json()
        assert data["detail"] == "Database error"

    @patch('apis.prompt_settings.get_current_user_profile')
    @patch('apis.prompt_settings.user_prompt_service')
    def test_update_user_prompt_success(self, mock_user_prompt_service, mock_get_user, client, mock_user_profile):
        """Test successful prompt configuration update."""
        mock_get_user.return_value = mock_user_profile
        mock_user_prompt_service.update_user_prompt.return_value = {"success": True, "message": "Updated successfully"}

        prompt_data = {
            "template": "Categorize email: Subject: {subject}, From: {sender}, Content: {content}",
            "model": "gpt-4",
            "temperature": 0.2,
            "max_tokens": 300,
            "timeout": 15
        }

        response = client.put("/settings/prompt", json=prompt_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        # Verify service was called with correct data
        mock_user_prompt_service.update_user_prompt.assert_called_once_with(
            mock_user_profile["user_id"], 
            prompt_data
        )

    @patch('apis.prompt_settings.get_current_user_profile')
    @patch('apis.prompt_settings.user_prompt_service')
    def test_update_user_prompt_with_defaults(self, mock_user_prompt_service, mock_get_user, client, mock_user_profile):
        """Test prompt update with default values."""
        mock_get_user.return_value = mock_user_profile
        mock_user_prompt_service.update_user_prompt.return_value = {"success": True}

        # Only provide required template field
        prompt_data = {
            "template": "Categorize: {subject}, {sender}, {content}"
        }

        response = client.put("/settings/prompt", json=prompt_data)

        assert response.status_code == 200
        
        # Verify default values were used
        call_args = mock_user_prompt_service.update_user_prompt.call_args[0][1]
        assert call_args["model"] == "gpt-3.5-turbo"
        assert call_args["temperature"] == 0.1
        assert call_args["max_tokens"] == 200
        assert call_args["timeout"] == 10

    def test_update_user_prompt_missing_required_variables(self, client):
        """Test prompt update with missing required variables."""
        prompt_data = {
            "template": "This template is missing required variables"
        }

        response = client.put("/settings/prompt", json=prompt_data)

        assert response.status_code == 400
        data = response.json()
        assert "Template must contain these variables" in data["detail"]
        assert "{subject}" in data["detail"]
        assert "{sender}" in data["detail"]
        assert "{content}" in data["detail"]

    def test_update_user_prompt_missing_some_variables(self, client):
        """Test prompt update with some missing required variables."""
        prompt_data = {
            "template": "Subject: {subject}, Content: {content}"  # Missing {sender}
        }

        response = client.put("/settings/prompt", json=prompt_data)

        assert response.status_code == 400
        data = response.json()
        assert "Template must contain these variables" in data["detail"]
        assert "{sender}" in data["detail"]

    def test_update_user_prompt_missing_template(self, client):
        """Test prompt update without template."""
        response = client.put("/settings/prompt", json={
            "model": "gpt-4"
        })

        assert response.status_code == 422

    @patch('apis.prompt_settings.get_current_user_profile')
    @patch('apis.prompt_settings.user_prompt_service')
    def test_update_user_prompt_service_failure(self, mock_user_prompt_service, mock_get_user, client, mock_user_profile):
        """Test prompt update with service failure."""
        mock_get_user.return_value = mock_user_profile
        mock_user_prompt_service.update_user_prompt.return_value = {
            "success": False, 
            "error": "Failed to update prompt"
        }

        prompt_data = {
            "template": "Valid template: {subject}, {sender}, {content}"
        }

        response = client.put("/settings/prompt", json=prompt_data)

        assert response.status_code == 500
        data = response.json()
        assert data["detail"] == "Failed to update prompt"

    @patch('apis.prompt_settings.get_current_user_profile')
    @patch('apis.prompt_settings.user_prompt_service')
    def test_update_user_prompt_service_exception(self, mock_user_prompt_service, mock_get_user, client, mock_user_profile):
        """Test prompt update with service exception."""
        mock_get_user.return_value = mock_user_profile
        mock_user_prompt_service.update_user_prompt.side_effect = Exception("Database connection failed")

        prompt_data = {
            "template": "Valid template: {subject}, {sender}, {content}"
        }

        response = client.put("/settings/prompt", json=prompt_data)

        assert response.status_code == 500
        data = response.json()
        assert data["detail"] == "Database connection failed"

    @patch('apis.prompt_settings.get_current_user_profile')
    @patch('apis.prompt_settings.user_prompt_service')
    def test_reset_user_prompt_success(self, mock_user_prompt_service, mock_get_user, client, mock_user_profile):
        """Test successful prompt reset to default."""
        mock_get_user.return_value = mock_user_profile
        mock_user_prompt_service.get_default_prompt_template.return_value = "Default template: {subject}, {sender}, {content}"
        mock_user_prompt_service.update_user_prompt.return_value = {"success": True}

        response = client.post("/settings/prompt/reset")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Prompt reset to default successfully"
        
        # Verify services were called correctly
        mock_user_prompt_service.get_default_prompt_template.assert_called_once()
        expected_reset_data = {
            'model': 'gpt-3.5-turbo',
            'temperature': 0.1,
            'max_tokens': 200,
            'timeout': 10,
            'template': "Default template: {subject}, {sender}, {content}"
        }
        mock_user_prompt_service.update_user_prompt.assert_called_once_with(
            mock_user_profile["user_id"], 
            expected_reset_data
        )

    @patch('apis.prompt_settings.get_current_user_profile')
    @patch('apis.prompt_settings.user_prompt_service')
    def test_reset_user_prompt_service_failure(self, mock_user_prompt_service, mock_get_user, client, mock_user_profile):
        """Test prompt reset with service failure."""
        mock_get_user.return_value = mock_user_profile
        mock_user_prompt_service.get_default_prompt_template.return_value = "Default template: {subject}, {sender}, {content}"
        mock_user_prompt_service.update_user_prompt.return_value = {
            "success": False, 
            "error": "Reset failed"
        }

        response = client.post("/settings/prompt/reset")

        assert response.status_code == 500
        data = response.json()
        assert data["detail"] == "Reset failed"

    @patch('apis.prompt_settings.get_current_user_profile')
    @patch('apis.prompt_settings.user_prompt_service')
    def test_reset_user_prompt_exception(self, mock_user_prompt_service, mock_get_user, client, mock_user_profile):
        """Test prompt reset with exception."""
        mock_get_user.return_value = mock_user_profile
        mock_user_prompt_service.get_default_prompt_template.side_effect = Exception("Failed to get default template")

        response = client.post("/settings/prompt/reset")

        assert response.status_code == 500
        data = response.json()
        assert data["detail"] == "Failed to get default template"

    @patch('apis.prompt_settings.get_current_user_profile')
    def test_validate_user_prompt_success(self, mock_get_user, client, mock_user_profile):
        """Test successful prompt validation."""
        mock_get_user.return_value = mock_user_profile

        validation_data = {
            "template": "Valid template: Subject: {subject}, From: {sender}, Content: {content}"
        }

        response = client.post("/settings/prompt/validate", json=validation_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Template is valid"
        assert "preview" in data
        assert "Test Subject" in data["preview"]
        assert "Test Sender" in data["preview"]
        assert "Test Content" in data["preview"]

    @patch('apis.prompt_settings.get_current_user_profile')
    def test_validate_user_prompt_missing_variables(self, mock_get_user, client, mock_user_profile):
        """Test prompt validation with missing required variables."""
        mock_get_user.return_value = mock_user_profile

        validation_data = {
            "template": "Invalid template missing variables"
        }

        response = client.post("/settings/prompt/validate", json=validation_data)

        assert response.status_code == 400
        data = response.json()
        assert "error" in data["detail"]
        assert "missing_variables" in data["detail"]
        assert "{subject}" in data["detail"]["missing_variables"]
        assert "{sender}" in data["detail"]["missing_variables"]
        assert "{content}" in data["detail"]["missing_variables"]

    @patch('apis.prompt_settings.get_current_user_profile')
    def test_validate_user_prompt_format_error(self, mock_get_user, client, mock_user_profile):
        """Test prompt validation with template formatting error."""
        mock_get_user.return_value = mock_user_profile

        validation_data = {
            "template": "Invalid template: {subject}, {sender}, {content}, {invalid_placeholder"  # Missing closing brace
        }

        response = client.post("/settings/prompt/validate", json=validation_data)

        assert response.status_code == 400
        data = response.json()
        assert "Template formatting error" in data["detail"]

    def test_validate_user_prompt_missing_template(self, client):
        """Test prompt validation without template."""
        response = client.post("/settings/prompt/validate", json={})

        assert response.status_code == 422

    @patch('apis.prompt_settings.get_current_user_profile')
    def test_validate_user_prompt_long_preview(self, mock_get_user, client, mock_user_profile):
        """Test prompt validation with long preview that gets truncated."""
        mock_get_user.return_value = mock_user_profile

        # Create a template that will generate a long preview
        long_template = "Very long template: " + "Subject: {subject}, " * 100 + "From: {sender}, Content: {content}"
        
        validation_data = {
            "template": long_template
        }

        response = client.post("/settings/prompt/validate", json=validation_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["preview"]) <= 503  # 500 + "..."
        assert data["preview"].endswith("...")

class TestPromptRequestModels:
    """Test prompt settings request/response models."""

    def test_prompt_update_request_valid(self):
        """Test valid prompt update request."""
        from apis.prompt_settings import PromptUpdateRequest
        
        request = PromptUpdateRequest(
            template="Test template: {subject}, {sender}, {content}",
            model="gpt-4",
            temperature=0.5,
            max_tokens=500,
            timeout=20
        )
        
        assert request.template == "Test template: {subject}, {sender}, {content}"
        assert request.model == "gpt-4"
        assert request.temperature == 0.5
        assert request.max_tokens == 500
        assert request.timeout == 20

    def test_prompt_update_request_defaults(self):
        """Test prompt update request with default values."""
        from apis.prompt_settings import PromptUpdateRequest
        
        request = PromptUpdateRequest(
            template="Test template: {subject}, {sender}, {content}"
        )
        
        assert request.template == "Test template: {subject}, {sender}, {content}"
        assert request.model == "gpt-3.5-turbo"
        assert request.temperature == 0.1
        assert request.max_tokens == 200
        assert request.timeout == 10

    def test_prompt_validation_request_valid(self):
        """Test valid prompt validation request."""
        from apis.prompt_settings import PromptValidationRequest
        
        request = PromptValidationRequest(
            template="Test template: {subject}, {sender}, {content}"
        )
        
        assert request.template == "Test template: {subject}, {sender}, {content}"

    def test_prompt_validation_request_missing_template(self):
        """Test prompt validation request without template."""
        from apis.prompt_settings import PromptValidationRequest
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            PromptValidationRequest()

class TestPromptSettingsAPIEdgeCases:
    """Test edge cases and error scenarios for prompt settings API."""

    def test_unauthorized_access(self, unauthenticated_client):
        """Test unauthorized access to prompt settings endpoints."""
        response = unauthenticated_client.get("/settings/prompt")
        assert response.status_code == 403  # FastAPI returns 403 for missing dependencies

        response = unauthenticated_client.put("/settings/prompt", json={"template": "test"})
        assert response.status_code == 403

        response = unauthenticated_client.post("/settings/prompt/reset")
        assert response.status_code == 403

        response = unauthenticated_client.post("/settings/prompt/validate", json={"template": "test"})
        assert response.status_code == 403

    def test_invalid_json_payloads(self, client):
        """Test invalid JSON payloads."""
        # Test with malformed JSON - this would be handled by FastAPI before reaching our endpoint
        response = client.put("/settings/prompt", 
                            data="invalid json",
                            headers={"Content-Type": "application/json"})
        assert response.status_code == 422

    def test_prompt_validation_edge_cases(self, client, mock_user_profile):
        """Test prompt validation edge cases."""
        with patch('apis.prompt_settings.get_current_user_profile', return_value=mock_user_profile):
            # Test with empty template
            response = client.post("/settings/prompt/validate", json={"template": ""})
            assert response.status_code == 400

            # Test with whitespace-only template
            response = client.post("/settings/prompt/validate", json={"template": "   "})
            assert response.status_code == 400

            # Test with valid variables but extra text
            response = client.post("/settings/prompt/validate", json={
                "template": "Extra content {subject} more content {sender} final {content}"
            })
            assert response.status_code == 200 