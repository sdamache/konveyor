"""
Tests for conversation context management in the Slack webhook handler.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from django.http import HttpResponse, JsonResponse
from django.test import RequestFactory

from konveyor.apps.bot.views import process_message, slack_webhook


@pytest.mark.django_db
def test_conversation_context_management():
    """Test that conversation context is correctly managed."""
    # Create a request factory
    factory = RequestFactory()

    # Create mock conversation manager
    mock_conversation_manager = MagicMock()
    mock_conversation_manager.get_user_conversations = AsyncMock(
        return_value=[{"id": "test_conversation_id"}]
    )
    mock_conversation_manager.add_message = AsyncMock(
        return_value={"id": "test_message_id"}
    )
    mock_conversation_manager.get_conversation_context = AsyncMock(
        return_value=[
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]
    )

    # Mock the SlackService and conversation manager
    with (
        patch("konveyor.apps.bot.views.slack_service") as mock_slack_service,
        patch(
            "konveyor.apps.bot.views.conversation_manager", mock_conversation_manager
        ),
        patch("konveyor.apps.bot.views.orchestrator") as mock_orchestrator,
    ):

        # Set up the mocks
        mock_slack_service.verify_request.return_value = True
        mock_slack_service.send_direct_message.return_value = {"ok": True}

        mock_orchestrator.process_request_sync.return_value = {
            "response": "Test response",
            "skill_name": "ChatSkill",
            "function_name": "answer",
            "success": True,
        }

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

        # Verify conversation manager methods were called
        mock_conversation_manager.get_user_conversations.assert_called_once()
        mock_conversation_manager.add_message.assert_called()  # Called twice (user + assistant)
        mock_conversation_manager.get_conversation_context.assert_called_once()

        # Verify orchestrator was called with conversation history
        context_arg = mock_orchestrator.process_request_sync.call_args[0][1]
        assert "conversation_history" in context_arg
        assert len(context_arg["conversation_history"]) == 2
        assert context_arg["conversation_history"][0]["role"] == "user"
        assert context_arg["conversation_history"][1]["role"] == "assistant"


def test_process_message_with_context():
    """Test that process_message includes conversation context."""
    # Create mock conversation manager
    mock_conversation_manager = MagicMock()
    mock_conversation_manager.get_user_conversations = AsyncMock(
        return_value=[{"id": "test_conversation_id"}]
    )
    mock_conversation_manager.add_message = AsyncMock(
        return_value={"id": "test_message_id"}
    )
    mock_conversation_manager.get_conversation_context = AsyncMock(
        return_value=[
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]
    )

    # Mock the orchestrator and conversation manager
    with (
        patch("konveyor.apps.bot.views.orchestrator") as mock_orchestrator,
        patch(
            "konveyor.apps.bot.views.conversation_manager", mock_conversation_manager
        ),
    ):

        # Set up the mock
        mock_orchestrator.process_request_sync.return_value = {
            "response": "Test response",
            "skill_name": "ChatSkill",
            "function_name": "answer",
            "success": True,
        }

        # Call process_message
        result = process_message("Hello, world!", "test_user", "test_channel")

        # Verify conversation manager methods were called
        mock_conversation_manager.get_user_conversations.assert_called_once()
        mock_conversation_manager.add_message.assert_called()  # Called twice (user + assistant)
        mock_conversation_manager.get_conversation_context.assert_called_once()

        # Verify orchestrator was called with conversation history
        context_arg = mock_orchestrator.process_request_sync.call_args[0][1]
        assert "conversation_history" in context_arg
        assert len(context_arg["conversation_history"]) == 2
        assert context_arg["conversation_history"][0]["role"] == "user"
        assert context_arg["conversation_history"][1]["role"] == "assistant"
