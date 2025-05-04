"""
Integration tests for the updated RAG service.

This module contains integration tests for the updated RAG service,
verifying that it works correctly with the new core components.
"""

import asyncio
from typing import Any, Dict, List  # noqa: F401
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from konveyor.core.rag.rag_service_updated import RAGService


# Test the RAG service with mocked dependencies
@pytest.mark.asyncio
async def test_rag_service_integration():
    """Test the RAG service integration with the new core components."""
    # Create a mock client manager
    mock_client_manager = MagicMock()
    mock_openai_client = MagicMock()
    mock_openai_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="Test response"))]
    )
    mock_client_manager.get_openai_client.return_value = mock_openai_client

    # Create a mock context service
    mock_context_service = MagicMock()
    mock_context_service.retrieve_context = AsyncMock(
        return_value=[
            {
                "content": "Test context",
                "source": "test_source.txt",
                "relevance_score": 0.95,
            }
        ]
    )
    mock_context_service.format_context.return_value = "Test context"

    # Create the RAG service with mocked dependencies
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
        patch(
            "konveyor.core.rag.rag_service_updated.ContextService",
            return_value=mock_context_service,
        ),
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
            "response": "Test response",
            "context_chunks": [
                {
                    "content": "Test context",
                    "source": "test_source.txt",
                    "relevance_score": 0.95,
                }
            ],
        }

        # Set up the mocks
        mock_create_manager.return_value = mock_conversation_manager
        mock_get_formatter.return_value = mock_formatter
        mock_get_generator.return_value = mock_response_generator

        # Create the RAG service
        rag_service = RAGService(mock_client_manager)

        # Replace the context service with our mock
        rag_service.context_service = mock_context_service

        # Wait for initialization to complete
        await asyncio.sleep(0.1)

        # Test generate_response with response generator
        response_data = await rag_service.generate_response(
            query="What is the capital of France?",
            conversation_id="test_conversation_id",
        )

        # Verify the response
        assert response_data is not None
        assert "answer" in response_data
        assert response_data["answer"] == "Test response"
        assert "sources" in response_data
        assert len(response_data["sources"]) == 1
        assert response_data["sources"][0]["source"] == "test_source.txt"
        assert "context_chunks" in response_data
        assert len(response_data["context_chunks"]) == 1
        assert "prompt_template" in response_data

        # Verify the response generator was called
        mock_response_generator.generate_response.assert_called_once()

        # Test generate_response without response generator
        # Replace the response generator with None to test the fallback
        rag_service.response_generator = None

        # Test generate_response
        response_data = await rag_service.generate_response(
            query="What is the capital of Germany?",
            conversation_id="test_conversation_id",
        )

        # Verify the response
        assert response_data is not None
        assert "answer" in response_data
        assert response_data["answer"] == "Test response"
        assert "sources" in response_data
        assert len(response_data["sources"]) == 1
        assert response_data["sources"][0]["source"] == "test_source.txt"
        assert "context_chunks" in response_data
        assert len(response_data["context_chunks"]) == 1
        assert "prompt_template" in response_data

        # Verify the context service was called
        mock_context_service.retrieve_context.assert_called()
        mock_context_service.format_context.assert_called()

        # Verify the OpenAI client was called
        mock_client_manager.get_openai_client.assert_called_once()
        mock_openai_client.chat.completions.create.assert_called_once()


# Run the tests
if __name__ == "__main__":
    asyncio.run(test_rag_service_integration())
