"""
Tests for the DocumentationNavigatorSkill.

This module contains tests for the DocumentationNavigatorSkill, including
unit tests and integration tests with the SearchService.
"""

import asyncio  # noqa: F401

# Mock the Django models and SearchService before importing DocumentationNavigatorSkill
import sys
from typing import Any, Dict, List  # noqa: F401, F401, F401
from unittest.mock import AsyncMock, MagicMock, patch  # noqa: F401, F401

import pytest

# Mock the Django models
sys.modules["konveyor.apps.documents.models"] = MagicMock()
sys.modules["konveyor.apps.search.services.search_service"] = MagicMock()
sys.modules["konveyor.core.documents.document_service"] = MagicMock()
sys.modules["konveyor.core.azure_utils.service"] = MagicMock()
sys.modules["konveyor.core.azure_utils.retry"] = MagicMock()
sys.modules["konveyor.core.azure_utils.mixins"] = MagicMock()
sys.modules["konveyor.core.conversation.factory"] = MagicMock()
sys.modules["konveyor.core.conversation.interface"] = MagicMock()


# Create a mock SearchService class
class MockSearchService:
    def __init__(self):
        pass

    def hybrid_search(self, query, top=5, load_full_content=True, filter_expr=None):
        return [
            {
                "id": "chunk1",
                "document_id": "doc1",
                "content": "This is sample content about onboarding.",
                "metadata": {"title": "Onboarding Guide"},
                "@search.score": 0.9,
            },
            {
                "id": "chunk2",
                "document_id": "doc2",
                "content": "More information about the onboarding process.",
                "metadata": {"title": "Employee Handbook"},
                "@search.score": 0.8,
            },
        ]


# Replace the SearchService with our mock
sys.modules["konveyor.apps.search.services.search_service"].SearchService = (
    MockSearchService
)


# Create a mock ConversationManager
class MockConversationManager:
    def __init__(self):
        self.conversations = {}
        self.messages = {}

    async def create_conversation(self, user_id=None, metadata=None):
        conversation_id = "test-conversation-id"
        self.conversations[conversation_id] = {
            "id": conversation_id,
            "user_id": user_id,
            "created_at": "2023-01-01T00:00:00",
            "metadata": metadata or {},
        }
        self.messages[conversation_id] = []
        return self.conversations[conversation_id]

    async def add_message(self, conversation_id, content, message_type, metadata=None):
        if conversation_id not in self.conversations:
            raise ValueError(f"Conversation not found: {conversation_id}")

        message = {
            "id": f"msg-{len(self.messages[conversation_id])}",
            "conversation_id": conversation_id,
            "content": content,
            "type": message_type,
            "created_at": "2023-01-01T00:00:00",
            "metadata": metadata or {},
        }

        self.messages[conversation_id].append(message)
        return message

    async def get_conversation_messages(
        self, conversation_id, limit=50, skip=0, include_metadata=True
    ):
        if conversation_id not in self.conversations:
            return []

        messages = self.messages.get(conversation_id, [])
        return messages[-limit:] if limit else messages

    async def get_conversation_context(
        self, conversation_id, format="string", max_messages=None
    ):
        if conversation_id not in self.conversations:
            return "" if format == "string" else []

        messages = self.messages.get(conversation_id, [])

        if format == "string":
            context = ""
            for message in messages:
                role = message["type"].capitalize()
                content = message["content"]
                context += f"{role}: {content}\n"
            return context.strip()
        else:
            return messages

    async def delete_conversation(self, conversation_id):
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            if conversation_id in self.messages:
                del self.messages[conversation_id]
            return True
        return False

    async def update_conversation_metadata(self, conversation_id, metadata):
        if conversation_id not in self.conversations:
            return None

        self.conversations[conversation_id]["metadata"] = metadata
        return self.conversations[conversation_id]

    async def get_user_conversations(self, user_id, limit=10, skip=0):
        user_conversations = [
            conv
            for conv in self.conversations.values()
            if conv.get("user_id") == user_id
        ]

        return user_conversations[skip : skip + limit]


# Create a mock ConversationManagerFactory
class MockConversationManagerFactory:
    @staticmethod
    async def create_manager():
        return MockConversationManager()


# Mock the ConversationManagerFactory
sys.modules["konveyor.core.conversation.factory"] = MagicMock()
sys.modules["konveyor.core.conversation.factory"].ConversationManagerFactory = (
    MockConversationManagerFactory
)

# Now import DocumentationNavigatorSkill
from konveyor.skills.documentation_navigator.DocumentationNavigatorSkill import (  # noqa: E402, E501
    DocumentationNavigatorSkill,
)


# Mock the Semantic Kernel
class MockKernel:
    def __init__(self):
        pass

    def add_plugin(self, plugin, plugin_name):
        return [MagicMock()]

    async def invoke(self, function, **kwargs):
        return "Mock response"


# Mock the create_kernel function
def mock_create_kernel():
    return MockKernel()


class TestDocumentationNavigatorSkill:
    """Tests for the DocumentationNavigatorSkill."""

    @pytest.fixture
    def skill(self):
        """Create a DocumentationNavigatorSkill with a mock SearchService."""
        # The SearchService is already mocked at the module level
        skill = DocumentationNavigatorSkill()
        return skill

    def test_initialization(self):
        """Test that the skill initializes correctly."""
        skill = DocumentationNavigatorSkill()
        assert skill is not None
        assert hasattr(skill, "search_service")

    @pytest.mark.asyncio
    async def test_search_documentation(self, skill):
        """Test the search_documentation function."""
        # Call the function
        result = await skill.search_documentation("onboarding process")

        # Check the result structure
        assert "original_query" in result
        assert "processed_query" in result
        assert "results" in result
        assert "result_count" in result
        assert "success" in result

        # Check the values
        assert result["original_query"] == "onboarding process"
        assert result["result_count"] == 2
        assert result["success"] is True
        assert len(result["results"]) == 2

    @pytest.mark.asyncio
    async def test_answer_question(self, skill):
        """Test the answer_question function."""
        # Call the function
        answer = await skill.answer_question("What is the onboarding process?")

        # Check that the answer contains expected elements
        assert "Based on the documentation" in answer
        assert "Sources:" in answer

    @pytest.mark.asyncio
    async def test_answer_question_with_conversation(self, skill):
        """Test the answer_question function with conversation context."""
        # Create a conversation
        conversation = await skill.create_conversation(user_id="test-user")
        conversation_id = conversation["id"]

        # Call the function with conversation ID
        answer = await skill.answer_question(
            "What is the onboarding process?", conversation_id=conversation_id
        )

        # Check that the answer contains expected elements
        assert "Based on the documentation" in answer
        assert "Sources:" in answer

        # Check that the conversation was updated
        conversation_manager = await skill._get_conversation_manager()
        messages = await conversation_manager.get_conversation_messages(conversation_id)
        assert len(messages) == 2  # User question and assistant response
        assert messages[0]["type"] == "user"
        assert messages[1]["type"] == "assistant"
        assert "What is the onboarding process?" in messages[0]["content"]

    @pytest.mark.asyncio
    async def test_continue_conversation(self, skill):
        """Test the continue_conversation function."""
        # Create a conversation
        conversation = await skill.create_conversation(user_id="test-user")
        conversation_id = conversation["id"]

        # Add initial question and answer
        await skill.answer_question(
            "What is the onboarding process?", conversation_id=conversation_id
        )

        # Call the continue_conversation function
        follow_up_answer = await skill.continue_conversation(
            "What should I do on my first day?", conversation_id=conversation_id
        )

        # Check that the answer contains expected elements
        assert "Based on the documentation" in follow_up_answer
        assert "Sources:" in follow_up_answer

        # Check that the conversation was updated
        conversation_manager = await skill._get_conversation_manager()
        messages = await conversation_manager.get_conversation_messages(conversation_id)
        assert len(messages) == 4  # Initial Q&A plus follow-up Q&A
        assert messages[2]["type"] == "user"
        assert messages[3]["type"] == "assistant"
        assert "What should I do on my first day?" in messages[2]["content"]

    @pytest.mark.asyncio
    async def test_create_conversation(self, skill):
        """Test the create_conversation function."""
        # Create a conversation
        conversation = await skill.create_conversation(user_id="test-user")

        # Check the conversation structure
        assert "id" in conversation
        assert conversation["user_id"] == "test-user"

    @pytest.mark.asyncio
    async def test_format_for_slack(self, skill):
        """Test the format_for_slack function."""
        # Call the function
        slack_format = await skill.format_for_slack("onboarding process")

        # Check the result structure
        assert "text" in slack_format
        assert "blocks" in slack_format

        # Check the blocks
        blocks = slack_format["blocks"]
        assert len(blocks) > 0

        # Check header block
        assert blocks[0]["type"] == "header"
        assert "Search Results" in blocks[0]["text"]["text"]

        # Check context block with query
        assert blocks[1]["type"] == "context"
        assert "Query" in blocks[1]["elements"][0]["text"]
        assert "onboarding process" in blocks[1]["elements"][0]["text"]

        # Check that we have result blocks
        result_blocks = [b for b in blocks if b.get("type") == "section"]
        assert len(result_blocks) > 0

        # Check that we have the footer with follow-up suggestion
        footer_blocks = [
            b for b in blocks if b.get("type") == "context" and "follow-up" in str(b)
        ]
        assert len(footer_blocks) > 0

    def test_preprocess_query(self, skill):
        """Test the query preprocessing function."""
        # Test with onboarding-related query
        processed = skill._preprocess_query("What is the onboarding process?")
        assert "onboarding" in processed
        # Check that it added enhancement terms
        assert "onboarding process" in processed or "employee onboarding" in processed

        # Test with new employee query
        processed = skill._preprocess_query(
            "I'm a new employee, what should I do first?"
        )
        assert "new employee" in processed
        assert "onboarding process" in processed or "first day" in processed

        # Test with technical terms preservation
        processed = skill._preprocess_query("How do I use the API with Kubernetes?")
        assert "api" in processed
        assert "kubernetes" in processed
        # Check that it preserved technical terms even with mixed case
        processed_mixed_case = skill._preprocess_query("How do I use the API with K8s?")
        assert "api" in processed_mixed_case
        assert "k8s" in processed_mixed_case

        # Test with regular query
        processed = skill._preprocess_query("How do I reset my password?")
        assert "reset" in processed
        assert "password" in processed

    def test_format_results(self, skill):
        """Test the result formatting function."""
        # Sample results
        results = [
            {
                "id": "chunk1",
                "document_id": "doc1",
                "content": "Sample content",
                "metadata": {"title": "Test Document"},
                "@search.score": 0.9,
            }
        ]

        # Format the results
        formatted = skill._format_results(results)

        # Check the formatting
        assert len(formatted) == 1
        assert formatted[0]["title"] == "Test Document"
        assert formatted[0]["citation"] == "[1] Test Document"


if __name__ == "__main__":
    # Run the tests
    pytest.main(["-xvs", __file__])
