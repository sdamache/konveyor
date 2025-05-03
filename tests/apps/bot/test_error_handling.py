"""
Tests for improved error handling in the Slack webhook handler.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch  # noqa: F401, F401

import pytest
from django.http import HttpResponse, JsonResponse  # noqa: F401
from django.test import RequestFactory

from konveyor.apps.bot.views import process_message, slack_webhook  # noqa: F401


@pytest.mark.django_db()
def test_error_handling_specific_errors():
    """Test that specific error types are handled correctly."""
    # Create a request factory
    factory = RequestFactory()

    # Mock the SlackService
    with (
        patch("konveyor.apps.bot.views.slack_service") as mock_slack_service,
        patch("konveyor.apps.bot.views.orchestrator") as mock_orchestrator,
    ):
        # Set up the mocks
        mock_slack_service.verify_request.return_value = True
        mock_slack_service.send_direct_message.return_value = {"ok": True}

        # Make orchestrator raise a specific error
        mock_orchestrator.process_request_sync.side_effect = ValueError(
            "Invalid input value"
        )

        # Test event callback with message
        post_data = {
            "type": "event_callback",
            "event_id": "test_event_id_specific_errors",
            "api_app_id": "test_app_id",
            "event": {
                "type": "message",
                "user": "test_user",
                "text": "Hello, world!",
                "channel": "test_channel",
                "channel_type": "im",
                "ts": "1234567890.123456",
                "client_msg_id": "test_client_msg_id_specific_errors",
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

        # Verify error message was sent with the specific error message
        assert mock_slack_service.send_direct_message.call_count == 1
        call_args = mock_slack_service.send_direct_message.call_args
        assert call_args[0][0] == "test_user"  # user
        assert (
            "I encountered an error while processing your request. Invalid input value"
            in call_args[0][1]
        )  # text


@pytest.mark.django_db()
def test_error_handling_slack_api_errors():
    """Test that Slack API errors are handled correctly."""
    # Create a request factory
    factory = RequestFactory()

    # Mock the SlackService
    with (
        patch("konveyor.apps.bot.views.slack_service") as mock_slack_service,
        patch("konveyor.apps.bot.views.orchestrator") as mock_orchestrator,
    ):
        # Set up the mocks
        mock_slack_service.verify_request.return_value = True

        # Make slack_service return an error
        mock_slack_service.send_direct_message.return_value = {
            "ok": False,
            "error": "channel_not_found",
        }

        # Make orchestrator return a successful response
        mock_orchestrator.process_request_sync.return_value = {
            "response": "Test response",
            "skill_name": "ChatSkill",
            "function_name": "answer",
            "success": True,
        }

        # Test event callback with message
        post_data = {
            "type": "event_callback",
            "event_id": "test_event_id_slack_api_errors",
            "api_app_id": "test_app_id",
            "event": {
                "type": "message",
                "user": "test_user",
                "text": "Hello, world!",
                "channel": "test_channel",
                "channel_type": "im",
                "ts": "1234567890.123456",
                "client_msg_id": "test_client_msg_id_slack_api_errors",
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

        # Verify send_direct_message was called
        assert mock_slack_service.send_direct_message.call_count == 1


@pytest.mark.django_db()
def test_error_handling_graceful_recovery():
    """Test that the system recovers gracefully from errors."""
    # Create a request factory
    factory = RequestFactory()

    # Mock the SlackService
    with (
        patch("konveyor.apps.bot.views.slack_service") as mock_slack_service,
        patch("konveyor.apps.bot.views.orchestrator") as mock_orchestrator,
    ):
        # Set up the mocks
        mock_slack_service.verify_request.return_value = True

        # Make orchestrator raise an error
        mock_orchestrator.process_request_sync.side_effect = Exception("Test error")

        # Test event callback with message
        post_data = {
            "type": "event_callback",
            "event_id": "test_event_id_graceful_recovery",
            "api_app_id": "test_app_id",
            "event": {
                "type": "message",
                "user": "test_user",
                "text": "Hello, world!",
                "channel": "test_channel",
                "channel_type": "im",
                "ts": "1234567890.123456",
                "client_msg_id": "test_client_msg_id_graceful_recovery",
            },
        }
        post_request = factory.post(
            "/api/bot/slack/events/",
            data=json.dumps(post_data),
            content_type="application/json",
        )

        # This should not raise an exception
        response = slack_webhook(post_request)

        # Verify the response
        assert response is not None
        assert isinstance(response, HttpResponse)
        assert response.status_code == 200

        # Verify that an error message was attempted to be sent
        assert mock_slack_service.send_direct_message.call_count >= 1
