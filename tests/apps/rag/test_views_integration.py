"""
Integration tests for the updated RAG views.

This module contains integration tests for the updated RAG views,
verifying that they work correctly with the new core components.
"""

import json  # noqa: F401
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from django.test import RequestFactory  # noqa: F401
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory

from konveyor.apps.rag.views_updated import ConversationViewSet


# Test the ConversationViewSet
@pytest.mark.asyncio()
async def test_conversation_viewset():
    """Test the ConversationViewSet."""
    # Create a request factory
    factory = APIRequestFactory()

    # Mock the AzureClientManager and RAGService
    with (
        patch(
            "konveyor.apps.rag.views_updated.AzureClientManager"
        ) as MockClientManager,
        patch("konveyor.apps.rag.views_updated.RAGService") as MockRAGService,
        patch(
            "konveyor.core.conversation.factory.ConversationManagerFactory.create_manager"  # noqa: E501
        ) as mock_create_manager,
        patch(
            "konveyor.core.formatters.factory.FormatterFactory.get_formatter"
        ) as mock_get_formatter,
    ):
        # Create mock client manager
        mock_client_manager = MagicMock()
        MockClientManager.return_value = mock_client_manager

        # Create mock RAG service
        mock_rag_service = MagicMock()
        mock_rag_service.generate_response = AsyncMock(
            return_value={
                "answer": "Test response",
                "sources": [
                    {"source": "test_source.txt", "page": 1, "relevance_score": 0.95}
                ],
                "context_chunks": [
                    {"content": "Test context", "source": "test_source.txt"}
                ],
                "prompt_template": "knowledge",
            }
        )
        MockRAGService.return_value = mock_rag_service

        # Create mock conversation manager
        mock_conversation_manager = AsyncMock()
        mock_conversation_manager.create_conversation.return_value = {
            "id": "test_conversation_id",
            "user_id": "test_user",
        }
        mock_conversation_manager.get_user_conversations.return_value = [
            {"id": "test_conversation_id", "user_id": "test_user"}
        ]
        mock_conversation_manager.get_conversation_messages.return_value = [
            {
                "id": "test_message_id",
                "conversation_id": "test_conversation_id",
                "content": "Test query",
                "type": "user",
            },
            {
                "id": "test_message_id2",
                "conversation_id": "test_conversation_id",
                "content": "Test response",
                "type": "assistant",
            },
        ]
        mock_create_manager.return_value = mock_conversation_manager

        # Create mock formatter
        mock_formatter = MagicMock()
        mock_formatter.format_message.return_value = {
            "text": "Formatted message",
            "blocks": [],
        }
        mock_get_formatter.return_value = mock_formatter

        # Create the viewset
        viewset = ConversationViewSet()

        # Wait for initialization to complete
        await viewset._init_conversation_manager()

        # Test create
        request = factory.post("/api/rag/conversations/")
        request.user = MagicMock(is_authenticated=True, id="test_user")
        response = await viewset.create(request)

        # Verify the response
        assert response is not None
        assert isinstance(response, Response)
        assert response.status_code == 200
        assert response.data == {"id": "test_conversation_id", "user_id": "test_user"}

        # Verify create_conversation was called
        mock_conversation_manager.create_conversation.assert_called_once_with(
            "test_user"
        )

        # Test list
        request = factory.get("/api/rag/conversations/")
        request.user = MagicMock(is_authenticated=True, id="test_user")
        response = await viewset.list(request)

        # Verify the response
        assert response is not None
        assert isinstance(response, Response)
        assert response.status_code == 200
        assert response.data == [{"id": "test_conversation_id", "user_id": "test_user"}]

        # Verify get_user_conversations was called
        mock_conversation_manager.get_user_conversations.assert_called_once_with(
            "test_user"
        )

        # Test ask
        request = factory.post(
            "/api/rag/conversations/test_conversation_id/ask/",
            {"query": "What is the capital of France?"},
        )
        request.user = MagicMock(is_authenticated=True, id="test_user")
        response = await viewset.ask(request, pk="test_conversation_id")

        # Verify the response
        assert response is not None
        assert isinstance(response, Response)
        assert response.status_code == 200
        assert response.data["response"] == "Test response"
        assert response.data["conversation_id"] == "test_conversation_id"
        assert "sources" in response.data
        assert len(response.data["sources"]) == 1
        assert response.data["sources"][0]["source"] == "test_source.txt"

        # Verify generate_response was called
        mock_rag_service.generate_response.assert_called_once_with(
            query="What is the capital of France?",
            conversation_id="test_conversation_id",
            template_type="knowledge",
            max_context_chunks=3,
        )

        # Test history
        request = factory.get("/api/rag/conversations/test_conversation_id/history/")
        request.user = MagicMock(is_authenticated=True, id="test_user")
        request.query_params = {"limit": "10"}
        response = await viewset.history(request, pk="test_conversation_id")

        # Verify the response
        assert response is not None
        assert isinstance(response, Response)
        assert response.status_code == 200
        assert len(response.data) == 2
        assert response.data[0]["content"] == "Test query"
        assert response.data[1]["content"] == "Test response"

        # Verify get_conversation_messages was called
        mock_conversation_manager.get_conversation_messages.assert_called_once_with(
            conversation_id="test_conversation_id", limit=10
        )

        # Test ask with error
        mock_rag_service.generate_response.side_effect = Exception("Test error")

        request = factory.post(
            "/api/rag/conversations/test_conversation_id/ask/",
            {"query": "What is the capital of France?"},
        )
        request.user = MagicMock(is_authenticated=True, id="test_user")
        response = await viewset.ask(request, pk="test_conversation_id")

        # Verify the response
        assert response is not None
        assert isinstance(response, Response)
        assert response.status_code == 500
        assert "error" in response.data
        assert "fallback_response" in response.data


# Run the tests
if __name__ == "__main__":
    import asyncio

    asyncio.run(test_conversation_viewset())
