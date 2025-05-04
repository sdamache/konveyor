"""
Integration tests for the updated bot views.

This module contains integration tests for the updated bot views,
verifying that they work correctly with the new core components.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch  # noqa: F401, F401

import pytest
from django.http import HttpResponse, JsonResponse
from django.test import RequestFactory

from konveyor.apps.bot.views_updated import process_message, root_handler, slack_webhook


# Test the root_handler
def test_root_handler():
    """Test the root_handler function."""
    # Create a request factory
    factory = RequestFactory()

    # Test GET request
    get_request = factory.get("/")
    response = root_handler(get_request)

    # Verify the response
    assert response is not None
    assert isinstance(response, HttpResponse)
    assert response.status_code == 200

    # Test POST request with URL verification
    post_data = {"type": "url_verification", "challenge": "test_challenge"}
    post_request = factory.post(
        "/", data=json.dumps(post_data), content_type="application/json"
    )
    response = root_handler(post_request)

    # Verify the response
    assert response is not None
    assert isinstance(response, JsonResponse)
    assert response.status_code == 200
    assert json.loads(response.content)["challenge"] == "test_challenge"

    # Test POST request with event callback
    post_data = {
        "type": "event_callback",
        "event": {"type": "message", "user": "test_user", "text": "Hello, world!"},
    }
    post_request = factory.post(
        "/", data=json.dumps(post_data), content_type="application/json"
    )
    response = root_handler(post_request)

    # Verify the response
    assert response is not None
    assert isinstance(response, HttpResponse)
    assert response.status_code == 200


# Test the slack_webhook function
@pytest.mark.django_db
def test_slack_webhook():
    """Test the slack_webhook function."""
    # Create a request factory
    factory = RequestFactory()

    # Mock the SlackService
    with (
        patch("konveyor.apps.bot.views_updated.slack_service") as mock_slack_service,
        patch(
            "konveyor.apps.bot.views_updated.process_message"
        ) as mock_process_message,
    ):
        # Set up the mocks
        mock_slack_service.verify_request.return_value = True
        mock_slack_service.send_direct_message.return_value = {"ok": True}
        mock_slack_service.send_message.return_value = {"ok": True}

        mock_process_message.return_value = {
            "response": "Test response",
            "skill_name": "ChatSkill",
            "conversation_id": "test_conversation_id",
            "success": True,
        }

        # Test URL verification
        post_data = {"type": "url_verification", "challenge": "test_challenge"}
        post_request = factory.post(
            "/api/bot/slack/events/",
            data=json.dumps(post_data),
            content_type="application/json",
        )
        response = slack_webhook(post_request)

        # Verify the response
        assert response is not None
        assert isinstance(response, JsonResponse)
        assert response.status_code == 200
        assert json.loads(response.content)["challenge"] == "test_challenge"

        # Test event callback with message
        post_data = {
            "type": "event_callback",
            "event_id": "test_event_id",
            "api_app_id": "test_app_id",
            "event": {
                "type": "message",
                "user": "test_user",
                "text": "Hello, world!",
                "channel": "test_channel",
                "channel_type": "im",
                "ts": "1234567890.123456",
                "client_msg_id": "test_client_msg_id",
            },
        }
        post_request = factory.post(
            "/api/bot/slack/events/",
            data=json.dumps(post_data),
            content_type="application/json",
        )
        response = slack_webhook(post_request)

        # Verify the response
        assert response is not None
        assert isinstance(response, HttpResponse)
        assert response.status_code == 200

        # Verify process_message was called
        mock_process_message.assert_called_once_with(
            "Hello, world!", "test_user", "test_channel"
        )

        # Verify send_direct_message was called
        mock_slack_service.send_direct_message.assert_called_once()

        # Test event callback with message in channel
        # Use a different event_id to avoid duplicate detection
        post_data["event_id"] = "test_event_id_2"
        post_data["event"]["channel_type"] = "channel"
        post_data["event"]["client_msg_id"] = "test_client_msg_id_2"
        post_request = factory.post(
            "/api/bot/slack/events/",
            data=json.dumps(post_data),
            content_type="application/json",
        )
        response = slack_webhook(post_request)

        # Verify the response
        assert response is not None
        assert isinstance(response, HttpResponse)
        assert response.status_code == 200

        # Verify send_message was called
        mock_slack_service.send_message.assert_called_once()


# Test the process_message function
def test_process_message():
    """Test the process_message function."""
    # Mock the orchestrator
    with (
        patch("konveyor.apps.bot.views_updated.orchestrator") as mock_orchestrator,
        patch(
            "konveyor.apps.bot.views_updated.conversation_manager"
        ) as mock_conversation_manager,  # noqa: F841
        patch("konveyor.apps.bot.views_updated.asyncio.run") as mock_asyncio_run,
    ):
        # Set up the mocks
        mock_orchestrator.process_request_sync.return_value = {
            "response": "Test response",
            "skill_name": "ChatSkill",
            "function_name": "chat",
            "success": True,
        }

        mock_asyncio_run.return_value = "test_conversation_id"

        # Test process_message
        result = process_message("Hello, world!", "test_user", "test_channel")

        # Verify the result
        assert result is not None
        assert "response" in result
        assert result["response"] == "Test response"
        assert "skill_name" in result
        assert result["skill_name"] == "ChatSkill"
        assert "function_name" in result
        assert result["function_name"] == "chat"
        assert "success" in result
        assert result["success"] is True
        assert "conversation_id" in result
        assert result["conversation_id"] == "test_conversation_id"

        # Verify the orchestrator was called
        mock_orchestrator.process_request_sync.assert_called_once()

        # Test process_message with error
        mock_orchestrator.process_request_sync.side_effect = ValueError("Test error")

        # Test process_message
        result = process_message("Hello, world!", "test_user", "test_channel")

        # Verify the result
        assert result is not None
        assert "response" in result
        assert "error" in result
        assert result["error"] == "Test error"
        assert "error_type" in result
        assert result["error_type"] == "ValueError"
        assert "success" in result
        assert result["success"] is False


# Run the tests
if __name__ == "__main__":
    test_root_handler()
    test_slack_webhook()
    test_process_message()
