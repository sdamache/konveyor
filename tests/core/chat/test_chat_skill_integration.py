"""
Integration tests for the updated ChatSkill.

This module contains integration tests for the updated ChatSkill,
verifying that it works correctly with the new core components.
"""

import asyncio
from typing import Any, Dict, List  # noqa: F401, F401, F401
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from konveyor.core.chat.skill_updated import ChatSkill


# Test the ChatSkill with mocked dependencies
@pytest.mark.asyncio()
async def test_chat_skill_integration():
    """Test the ChatSkill integration with the new core components."""
    # Create a mock kernel
    mock_kernel = MagicMock()

    # Create a ChatSkill with the mock kernel
    with (
        patch(
            "konveyor.core.conversation.factory.ConversationManagerFactory.create_manager"  # noqa: E501
        ) as mock_create_manager,
        patch(
            "konveyor.core.formatters.factory.FormatterFactory.get_formatter"
        ) as mock_get_formatter,
        patch(
            "konveyor.core.generation.factory.ResponseGeneratorFactory.get_generator"
        ) as mock_get_generator,
    ):
        # Create mock conversation manager
        mock_conversation_manager = AsyncMock()
        mock_conversation_manager.create_conversation.return_value = {
            "id": "test_conversation_id"
        }
        mock_conversation_manager.get_conversation_context.return_value = (
            "User: Test query\nAssistant: Test response"
        )
        mock_conversation_manager.add_message.return_value = {"id": "test_message_id"}

        # Create mock formatter
        mock_formatter = MagicMock()
        mock_formatter.format_message.return_value = {
            "text": "Formatted message",
            "blocks": [],
        }

        # Create mock response generator
        mock_response_generator = AsyncMock()
        mock_response_generator.generate_response.return_value = {
            "response": "Test response"
        }

        # Set up the mocks
        mock_create_manager.return_value = mock_conversation_manager
        mock_get_formatter.return_value = mock_formatter
        mock_get_generator.return_value = mock_response_generator

        # Create the ChatSkill
        chat_skill = ChatSkill(kernel=mock_kernel)

        # Wait for initialization to complete
        await asyncio.sleep(0.1)

        # Test answer_question
        response = await chat_skill.answer_question("What is the capital of France?")

        # Verify the response
        assert response is not None
        assert "Test response" in response

        # Verify the response generator was called
        mock_response_generator.generate_response.assert_called_once()

        # Test chat
        chat_result = await chat_skill.chat("Hello, how are you?")

        # Verify the result
        assert chat_result is not None
        assert "response" in chat_result
        assert "Test response" in chat_result["response"]
        assert "conversation_id" in chat_result
        assert "skill_name" in chat_result
        assert chat_result["skill_name"] == "ChatSkill"
        assert "function_name" in chat_result
        assert chat_result["function_name"] == "chat"
        assert "success" in chat_result
        assert chat_result["success"] is True

        # Verify the response generator was called
        assert mock_response_generator.generate_response.call_count == 2

        # Test format_for_slack
        formatted = chat_skill.format_for_slack("Test message")

        # Verify the formatter was called
        mock_formatter.format_message.assert_called_once_with(
            text="Test message", include_blocks=True
        )

        # Verify the result
        assert formatted is not None
        assert "text" in formatted
        assert formatted["text"] == "Formatted message"
        assert "blocks" in formatted

        # Test greet
        greeting = await chat_skill.greet("Test User")

        # Verify the greeting
        assert greeting is not None
        assert "Hello, Test User" in greeting

        # Test format_as_bullet_list
        bullet_list = chat_skill.format_as_bullet_list("Item 1\nItem 2\nItem 3")

        # Verify the bullet list
        assert bullet_list is not None
        assert "• Item 1" in bullet_list
        assert "• Item 2" in bullet_list
        assert "• Item 3" in bullet_list


# Run the tests
if __name__ == "__main__":
    asyncio.run(test_chat_skill_integration())
