"""Tests for inbox API endpoints."""

import pytest
from fastapi import HTTPException
from unittest.mock import Mock, patch
from tests.factories import generate_gmail_thread, EmailDetailsFactory, EmailFactory

class TestInboxAPI:
    """Test inbox API endpoints."""

    @patch('apis.inbox.GoogleService')
    def test_get_inbox_success(self, mock_google_service_class, client_with_user, mock_user_profile):
        """Test successful inbox retrieval."""
        # Setup mocks
        mock_google_service = Mock()
        mock_google_service_class.return_value = mock_google_service
        
        # Create mock threads
        mock_threads = [
            generate_gmail_thread(email_count=3),
            generate_gmail_thread(email_count=2),
            generate_gmail_thread(email_count=1)
        ]
        mock_google_service.get_inbox_threads.return_value = mock_threads

        # Make request
        response = client_with_user.get("/inbox/")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert "threads" in data
        assert "thread_count" in data
        assert "total_emails" in data
        assert "limit" in data
        assert "offset" in data
        assert "source" in data
        
        assert data["thread_count"] == 3
        assert data["total_emails"] == 6  # 3 + 2 + 1
        assert data["limit"] == 50
        assert data["offset"] == 0
        assert data["source"] == "database"
        
        # Verify service was called correctly
        mock_google_service_class.assert_called_once_with(internal_user_id=mock_user_profile["user_id"])
        mock_google_service.get_inbox_threads.assert_called_once_with(limit=50, offset=0)

    @patch('apis.inbox.get_current_user_profile')
    @patch('apis.inbox.GoogleService')
    def test_get_inbox_with_pagination(self, mock_google_service_class, mock_get_user, client, mock_user_profile):
        """Test inbox retrieval with pagination parameters."""
        mock_get_user.return_value = mock_user_profile
        mock_google_service = Mock()
        mock_google_service_class.return_value = mock_google_service
        mock_google_service.get_inbox_threads.return_value = []

        response = client.get("/inbox/?limit=10&offset=20")

        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 10
        assert data["offset"] == 20
        
        mock_google_service.get_inbox_threads.assert_called_once_with(limit=10, offset=20)

    @patch('apis.inbox.get_current_user_profile')
    @patch('apis.inbox.GoogleService')
    def test_get_emails_success(self, mock_google_service_class, mock_get_user, client, mock_user_profile):
        """Test successful individual emails retrieval."""
        mock_get_user.return_value = mock_user_profile
        mock_google_service = Mock()
        mock_google_service_class.return_value = mock_google_service
        
        # Create mock emails
        mock_emails = [EmailFactory().model_dump() for _ in range(3)]
        mock_google_service.get_inbox_emails.return_value = mock_emails

        response = client.get("/inbox/emails")

        assert response.status_code == 200
        data = response.json()
        assert "emails" in data
        assert "count" in data
        assert "limit" in data
        assert "offset" in data
        assert "source" in data
        
        assert data["count"] == 3
        assert data["limit"] == 50
        assert data["offset"] == 0
        assert data["source"] == "database"
        
        mock_google_service.get_inbox_emails.assert_called_once_with(limit=50, offset=0)

    @patch('apis.inbox.get_current_user_profile')
    @patch('apis.inbox.GoogleService')
    def test_sync_emails_success(self, mock_google_service_class, mock_get_user, client, mock_user_profile):
        """Test successful email sync."""
        mock_get_user.return_value = mock_user_profile
        mock_google_service = Mock()
        mock_google_service_class.return_value = mock_google_service
        
        # Mock fetched emails
        mock_emails = [EmailDetailsFactory().to_dict() for _ in range(5)]
        mock_google_service.fetch_gmail_emails.return_value = mock_emails

        response = client.post("/inbox/emails/sync")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "emails_synced" in data
        assert "source" in data
        
        assert data["emails_synced"] == 5
        assert data["source"] == "gmail_api"
        assert "Successfully synced 5 emails" in data["message"]
        
        mock_google_service.fetch_gmail_emails.assert_called_once_with(max_results=50, only_new=True)

    @patch('apis.inbox.get_current_user_profile')
    @patch('apis.inbox.GoogleService')
    def test_sync_emails_with_custom_max_results(self, mock_google_service_class, mock_get_user, client, mock_user_profile):
        """Test email sync with custom max results."""
        mock_get_user.return_value = mock_user_profile
        mock_google_service = Mock()
        mock_google_service_class.return_value = mock_google_service
        mock_google_service.fetch_gmail_emails.return_value = []

        response = client.post("/inbox/emails/sync?max_results=100")

        assert response.status_code == 200
        mock_google_service.fetch_gmail_emails.assert_called_once_with(max_results=100, only_new=True)

    @patch('apis.inbox.get_current_user_profile')
    @patch('apis.inbox.GoogleService')
    def test_mark_email_as_read_success(self, mock_google_service_class, mock_get_user, client, mock_user_profile):
        """Test successfully marking an email as read."""
        mock_get_user.return_value = mock_user_profile
        mock_google_service = Mock()
        mock_google_service_class.return_value = mock_google_service
        mock_google_service.mark_email_as_read.return_value = True

        email_id = "test_email_id"
        response = client.put(f"/inbox/email/{email_id}/read")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Email marked as read"
        assert data["email_id"] == email_id
        
        mock_google_service.mark_email_as_read.assert_called_once_with(email_id)

    @patch('apis.inbox.get_current_user_profile')
    @patch('apis.inbox.GoogleService')
    def test_mark_email_as_read_not_found(self, mock_google_service_class, mock_get_user, client, mock_user_profile):
        """Test marking non-existent email as read."""
        mock_get_user.return_value = mock_user_profile
        mock_google_service = Mock()
        mock_google_service_class.return_value = mock_google_service
        mock_google_service.mark_email_as_read.return_value = False

        response = client.put("/inbox/email/nonexistent_id/read")

        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Email not found"

    @patch('apis.inbox.get_current_user_profile')
    @patch('apis.inbox.GoogleService')
    def test_mark_thread_as_read_success(self, mock_google_service_class, mock_get_user, client, mock_user_profile):
        """Test successfully marking a thread as read."""
        mock_get_user.return_value = mock_user_profile
        mock_google_service = Mock()
        mock_google_service_class.return_value = mock_google_service
        mock_google_service.mark_thread_as_read.return_value = 3

        thread_id = "test_thread_id"
        response = client.put(f"/inbox/thread/{thread_id}/read")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Marked 3 emails as read in thread"
        assert data["thread_id"] == thread_id
        
        mock_google_service.mark_thread_as_read.assert_called_once_with(thread_id)

    @patch('apis.inbox.get_current_user_profile')
    @patch('apis.inbox.GoogleService')
    def test_get_single_email_success(self, mock_google_service_class, mock_get_user, client, mock_user_profile):
        """Test successfully retrieving a single email."""
        mock_get_user.return_value = mock_user_profile
        mock_google_service = Mock()
        mock_google_service_class.return_value = mock_google_service
        
        mock_email = EmailFactory().model_dump()
        mock_google_service.get_single_email_from_db.return_value = mock_email

        email_id = "test_email_id"
        response = client.get(f"/inbox/email/{email_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(mock_email["id"])  # Convert UUID to string for comparison
        assert data["subject"] == mock_email["subject"]
        
        mock_google_service.get_single_email_from_db.assert_called_once_with(email_id)

    @patch('apis.inbox.get_current_user_profile')
    @patch('apis.inbox.GoogleService')
    def test_get_single_email_not_found(self, mock_google_service_class, mock_get_user, client, mock_user_profile):
        """Test retrieving non-existent email."""
        mock_get_user.return_value = mock_user_profile
        mock_google_service = Mock()
        mock_google_service_class.return_value = mock_google_service
        mock_google_service.get_single_email_from_db.return_value = None

        response = client.get("/inbox/email/nonexistent_id")

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]

    @patch('apis.inbox.get_current_user_profile')
    @patch('apis.inbox.GoogleService')
    def test_get_thread_success(self, mock_google_service_class, mock_get_user, client, mock_user_profile):
        """Test successfully retrieving a thread."""
        mock_get_user.return_value = mock_user_profile
        mock_google_service = Mock()
        mock_google_service_class.return_value = mock_google_service
        
        mock_thread = generate_gmail_thread(email_count=3)
        mock_google_service.get_thread_by_id.return_value = mock_thread

        thread_id = "test_thread_id"
        response = client.get(f"/inbox/thread/{thread_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["thread_id"] == mock_thread["thread_id"]
        assert data["email_count"] == mock_thread["email_count"]
        
        mock_google_service.get_thread_by_id.assert_called_once_with(thread_id)

    @patch('apis.inbox.get_current_user_profile')
    @patch('apis.inbox.GoogleService')
    def test_get_thread_not_found(self, mock_google_service_class, mock_get_user, client, mock_user_profile):
        """Test retrieving non-existent thread."""
        mock_get_user.return_value = mock_user_profile
        mock_google_service = Mock()
        mock_google_service_class.return_value = mock_google_service
        mock_google_service.get_thread_by_id.return_value = None

        response = client.get("/inbox/thread/nonexistent_id")

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]

    @patch('apis.inbox.get_current_user_profile')
    @patch('apis.inbox.GoogleService')
    def test_reply_to_email_success(self, mock_google_service_class, mock_get_user, client, mock_user_profile):
        """Test successfully replying to an email."""
        mock_get_user.return_value = mock_user_profile
        mock_google_service = Mock()
        mock_google_service_class.return_value = mock_google_service
        mock_google_service.send_email_reply.return_value = {"success": True}

        email_id = "test_email_id"
        reply_data = {
            "reply_body": "Thank you for your email!",
            "reply_subject": "Re: Test Subject"
        }

        response = client.post(f"/inbox/email/{email_id}/reply", json=reply_data)

        assert response.status_code == 200
        data = response.json()
        assert "Successfully sent reply" in data["message"]
        assert data["email_id"] == email_id
        
        mock_google_service.send_email_reply.assert_called_once_with(
            original_email_id=email_id,
            reply_body="Thank you for your email!",
            reply_subject="Re: Test Subject",
            to=None,
            cc=None,
            bcc=None
        )

    @patch('apis.inbox.get_current_user_profile')
    @patch('apis.inbox.GoogleService')
    def test_reply_to_email_with_custom_recipients(self, mock_google_service_class, mock_get_user, client, mock_user_profile):
        """Test replying to email with custom recipients."""
        mock_get_user.return_value = mock_user_profile
        mock_google_service = Mock()
        mock_google_service_class.return_value = mock_google_service
        mock_google_service.send_email_reply.return_value = {"success": True}

        email_id = "test_email_id"
        reply_data = {
            "reply_body": "Thank you for your email!",
            "to": ["custom@example.com"],
            "cc": ["cc@example.com"],
            "bcc": ["bcc@example.com"]
        }

        response = client.post(f"/inbox/email/{email_id}/reply", json=reply_data)

        assert response.status_code == 200
        
        mock_google_service.send_email_reply.assert_called_once_with(
            original_email_id=email_id,
            reply_body="Thank you for your email!",
            reply_subject="",
            to=["custom@example.com"],
            cc=["cc@example.com"],
            bcc=["bcc@example.com"]
        )

    @patch('apis.inbox.get_current_user_profile')
    @patch('apis.inbox.GoogleService')
    def test_reply_to_email_failure(self, mock_google_service_class, mock_get_user, client, mock_user_profile):
        """Test email reply failure."""
        mock_get_user.return_value = mock_user_profile
        mock_google_service = Mock()
        mock_google_service_class.return_value = mock_google_service
        mock_google_service.send_email_reply.return_value = {"error": "Failed to send email"}

        email_id = "test_email_id"
        reply_data = {
            "reply_body": "Thank you for your email!"
        }

        response = client.post(f"/inbox/email/{email_id}/reply", json=reply_data)

        assert response.status_code == 400
        data = response.json()
        assert data["detail"] == "Failed to send email"

    def test_reply_to_email_missing_body(self, client):
        """Test email reply with missing body."""
        response = client.post("/inbox/email/test_id/reply", json={})

        assert response.status_code == 422

class TestEmailReplyRequest:
    """Test EmailReplyRequest model validation."""

    def test_valid_reply_request(self):
        """Test valid email reply request."""
        from apis.inbox import EmailReplyRequest
        
        request = EmailReplyRequest(
            reply_body="Thank you for your message!",
            reply_subject="Re: Test",
            to=["recipient@example.com"],
            cc=["cc@example.com"],
            bcc=["bcc@example.com"]
        )
        
        assert request.reply_body == "Thank you for your message!"
        assert request.reply_subject == "Re: Test"
        assert request.to == ["recipient@example.com"]
        assert request.cc == ["cc@example.com"]
        assert request.bcc == ["bcc@example.com"]

    def test_minimal_reply_request(self):
        """Test minimal email reply request with only required fields."""
        from apis.inbox import EmailReplyRequest
        
        request = EmailReplyRequest(reply_body="Thank you!")
        
        assert request.reply_body == "Thank you!"
        assert request.reply_subject is None
        assert request.to is None
        assert request.cc is None
        assert request.bcc is None

    def test_reply_request_missing_body(self):
        """Test email reply request without body."""
        from apis.inbox import EmailReplyRequest
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            EmailReplyRequest() 