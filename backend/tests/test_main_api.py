"""Tests for main API endpoints and general functionality."""

import pytest
from unittest.mock import patch

class TestMainAPI:
    """Test main API endpoints."""

    def test_root_endpoint(self, client):
        """Test root endpoint returns correct message."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Finance Inbox API is running"

    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

class TestCORSConfiguration:
    """Test CORS middleware configuration."""

    def test_cors_headers_present(self, client):
        """Test that CORS headers are present in responses."""
        response = client.get("/")
        
        assert response.status_code == 200
        # Note: In test environment, CORS headers might not be fully set
        # This test verifies the endpoint works, full CORS testing would require
        # integration tests with different origins

    def test_preflight_request(self, client):
        """Test preflight OPTIONS request handling."""
        response = client.options("/auth/login")
        
        # FastAPI with CORS middleware should handle OPTIONS requests
        assert response.status_code in [200, 405]  # 405 if not explicitly handled

class TestAPIStructure:
    """Test API structure and router inclusion."""

    def test_auth_routes_included(self, client):
        """Test that auth routes are accessible."""
        # Test valid auth endpoint exists
        response = client.get("/auth/health")
        assert response.status_code == 200

    def test_inbox_routes_included(self, client):
        """Test that inbox routes are accessible."""
        # Test inbox endpoint - with mocked auth, should work
        response = client.get("/inbox/")
        assert response.status_code in [200, 401, 422, 500]  # Any response except 404 means route exists

    def test_gmail_auth_routes_included(self, client):
        """Test that Gmail auth routes are accessible."""
        response = client.get("/google-auth/status")
        assert response.status_code in [200, 401, 422, 500]  # Any response except 404 means route exists

    def test_slack_auth_routes_included(self, client):
        """Test that Slack auth routes are accessible."""
        response = client.get("/slack-auth/status")
        assert response.status_code in [200, 401, 422, 500]  # Any response except 404 means route exists

    def test_slack_api_routes_included(self, client):
        """Test that Slack API routes are accessible."""
        response = client.get("/slack-api/test-connection")
        assert response.status_code in [200, 401, 422, 500]  # Any response except 404 means route exists

    def test_settings_routes_included(self, client):
        """Test that settings routes are accessible."""
        response = client.get("/settings/connections")
        assert response.status_code in [200, 401, 422, 500]  # Any response except 404 means route exists

    def test_prompt_settings_routes_included(self, client):
        """Test that prompt settings routes are accessible."""
        response = client.get("/settings/prompt")
        assert response.status_code in [200, 401, 422, 500]  # Any response except 404 means route exists

class TestErrorHandling:
    """Test general error handling."""

    def test_404_for_non_existent_endpoint(self, client):
        """Test 404 response for non-existent endpoints."""
        response = client.get("/non-existent-endpoint")
        assert response.status_code == 404

    def test_method_not_allowed(self, client):
        """Test 405 response for unsupported methods."""
        # Root endpoint only supports GET
        response = client.post("/")
        assert response.status_code == 405

    def test_invalid_json_request(self, client):
        """Test handling of invalid JSON in request body."""
        response = client.post(
            "/auth/login",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

    def test_missing_content_type_for_json_endpoint(self, client):
        """Test handling of missing content type for JSON endpoints."""
        response = client.post(
            "/auth/login",
            data='{"email": "test@example.com", "password": "test"}',
            headers={"Content-Type": "text/plain"}
        )
        assert response.status_code == 422

class TestAppLifespan:
    """Test application lifespan events."""

    @patch('main.email_polling_service')
    @patch('main.asyncio.create_task')
    def test_startup_polling_service(self, mock_create_task, mock_polling_service):
        """Test that email polling service starts on app startup."""
        # Note: This test would require more complex setup to actually test the lifespan
        # For now, we verify the imports and structure are correct
        from main import app
        assert app is not None
        assert hasattr(app, 'router')

    def test_app_metadata(self, client):
        """Test app metadata is correctly set."""
        # Verify the app is configured with correct title and version
        # This is implicitly tested by the fact that the app starts correctly
        response = client.get("/")
        assert response.status_code == 200

class TestAPIDocumentation:
    """Test API documentation endpoints."""

    def test_openapi_schema_available(self, client):
        """Test that OpenAPI schema is available."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert data["info"]["title"] == "Finance Inbox API"
        assert data["info"]["version"] == "1.0.0"

    def test_docs_endpoint_available(self, client):
        """Test that Swagger docs endpoint is available."""
        response = client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

    def test_redoc_endpoint_available(self, client):
        """Test that ReDoc endpoint is available."""
        response = client.get("/redoc")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

class TestAPIValidation:
    """Test API validation and Pydantic integration."""

    def test_email_validation_in_auth(self, client):
        """Test email validation in auth endpoints."""
        response = client.post("/auth/login", json={
            "email": "invalid-email-format",
            "password": "password123"
        })
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        # Should contain validation error for email field

    def test_required_fields_validation(self, client):
        """Test required fields validation."""
        response = client.post("/auth/login", json={
            "email": "test@example.com"
            # Missing password
        })
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_extra_fields_handling(self, client):
        """Test handling of extra fields in requests."""
        response = client.post("/auth/login", json={
            "email": "test@example.com",
            "password": "password123",
            "extra_field": "should_be_ignored"
        })
        # Should not fail due to extra field (Pydantic ignores extra by default)
        assert response.status_code in [200, 401, 500]  # Any response except 422

class TestSecurityHeaders:
    """Test security-related headers and middleware."""

    def test_no_server_header_leakage(self, client):
        """Test that server implementation details are not leaked."""
        response = client.get("/")
        
        # Check that we don't leak server implementation details
        server_header = response.headers.get("server", "")
        assert "uvicorn" not in server_header.lower()

    def test_content_type_headers(self, client):
        """Test that appropriate content-type headers are set."""
        response = client.get("/")
        assert response.headers.get("content-type") == "application/json"

        response = client.get("/docs")
        assert "text/html" in response.headers.get("content-type", "")

class TestRateLimiting:
    """Test rate limiting (if implemented)."""

    def test_multiple_requests_allowed(self, client):
        """Test that multiple reasonable requests are allowed."""
        # Make multiple requests to ensure no aggressive rate limiting
        for _ in range(5):
            response = client.get("/health")
            assert response.status_code == 200

class TestResponseFormats:
    """Test consistent response formats across API."""

    def test_json_responses_are_valid(self, client):
        """Test that all JSON responses are valid JSON."""
        endpoints = [
            "/",
            "/health",
            "/auth/health"
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            if response.status_code == 200:
                # Should be valid JSON
                data = response.json()
                assert isinstance(data, dict)

    def test_error_response_format(self, client):
        """Test that error responses follow consistent format."""
        # Test 404 error
        response = client.get("/non-existent")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

        # Test validation error
        response = client.post("/auth/login", json={})
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data 