"""
Tests for the DocumentationNavigatorSkill with conversation memory integration.

This module tests the conversation memory features of the DocumentationNavigatorSkill,
including creating conversations, adding messages, and handling follow-up questions.
"""

# Removed: import asyncio
# Mock the necessary modules before importing DocumentationNavigatorSkill
import sys
import uuid
from datetime import datetime

# Removed: from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch

import pytest

from konveyor.skills.documentation_navigator.DocumentationNavigatorSkill import (
    DocumentationNavigatorSkill,
)

sys.modules["konveyor.apps.documents.models"] = MagicMock()
sys.modules["konveyor.apps.search.services.search_service"] = MagicMock()
sys.modules["konveyor.core.documents.document_service"] = MagicMock()
sys.modules["konveyor.core.azure_utils.service"] = MagicMock()
sys.modules["konveyor.core.azure_utils.retry"] = MagicMock()
sys.modules["konveyor.core.azure_utils.mixins"] = MagicMock()


# Create a mock ConversationManager class
class MockConversationManager:
    """Mock implementation of the ConversationInterface for testing."""

    def __init__(self):
        """Initialize the mock conversation manager."""
        self.conversations = {}
        self.messages = {}

    async def create_conversation(self, user_id=None, metadata=None):
        """Create a new conversation."""
        conversation_id = str(uuid.uuid4())
        self.conversations[conversation_id] = {
            "id": conversation_id,
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "metadata": metadata or {},
        }
        self.messages[conversation_id] = []
        return self.conversations[conversation_id]

    async def add_message(self, conversation_id, content, message_type, metadata=None):
        """Add a message to a conversation."""
        if conversation_id not in self.conversations:
            raise ValueError(f"Conversation not found: {conversation_id}")

        message = {
            "id": f"msg-{len(self.messages[conversation_id])}",
            "conversation_id": conversation_id,
            "content": content,
            "type": message_type,
            "created_at": datetime.now().isoformat(),
            "metadata": metadata or {},
        }

        self.messages[conversation_id].append(message)
        return message

    async def get_conversation_messages(
        self, conversation_id, limit=50, skip=0, include_metadata=True
    ):
        """Get messages for a conversation."""
        if conversation_id not in self.conversations:
            return []

        messages = self.messages.get(conversation_id, [])
        return messages[-limit:] if limit else messages

    async def get_conversation_context(
        self, conversation_id, format="string", max_messages=None
    ):
        """Get the conversation context in the specified format."""
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
        """Delete a conversation and all its messages."""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            if conversation_id in self.messages:
                del self.messages[conversation_id]
            return True
        return False

    async def update_conversation_metadata(self, conversation_id, metadata):
        """Update the metadata for a conversation."""
        if conversation_id not in self.conversations:
            return None

        self.conversations[conversation_id]["metadata"] = metadata
        return self.conversations[conversation_id]

    async def get_user_conversations(self, user_id, limit=10, skip=0):
        """Get conversations for a user."""
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


# Create a mock SearchService class
class MockSearchService:
    """Mock implementation of the SearchService for testing."""

    def __init__(self):
        """Initialize the mock SearchService."""
        # Sample documentation data
        self.documents = [
            {
                "id": "doc1-chunk1",
                "document_id": "doc1",
                "content": "Onboarding is the process of integrating new employees into the company. It includes orientation, training, and introduction to company culture.",
                "metadata": {"title": "Onboarding Guide"},
                "@search.score": 0.95,
            },
            {
                "id": "doc1-chunk2",
                "document_id": "doc1",
                "content": "On your first day, you should complete the HR paperwork, set up your workstation, and meet with your manager and team members.",
                "metadata": {"title": "Onboarding Guide - First Day"},
                "@search.score": 0.9,
            },
            {
                "id": "doc2-chunk1",
                "document_id": "doc2",
                "content": "The IT department will help you set up your computer, email, and access to company systems. Contact the IT helpdesk at it@example.com.",
                "metadata": {"title": "IT Setup Guide"},
                "@search.score": 0.85,
            },
            {
                "id": "doc3-chunk1",
                "document_id": "doc3",
                "content": "Company policies include guidelines for remote work, time off, and expense reimbursement. All policies are available in the employee handbook.",
                "metadata": {"title": "Company Policies"},
                "@search.score": 0.8,
            },
            {
                "id": "doc4-chunk1",
                "document_id": "doc4",
                "content": "The development environment setup includes installing Git, Docker, and VS Code. Follow the instructions in the README file.",
                "metadata": {"title": "Development Environment Setup"},
                "@search.score": 0.75,
            },
        ]

    def hybrid_search(self, query, top=5, load_full_content=True, filter_expr=None):
        """Perform a hybrid search on the mock documents."""
        # Simple keyword matching for demonstration
        results = []
        query_terms = query.lower().split()

        for doc in self.documents:
            content = doc["content"].lower()
            title = doc["metadata"]["title"].lower()

            # Calculate a simple relevance score based on term frequency
            score = 0
            for term in query_terms:
                if term in content:
                    score += 0.1
                if term in title:
                    score += 0.2

            # Only include documents with some relevance
            if score > 0:
                # Create a copy of the document with the calculated score
                result = doc.copy()
                result["@search.score"] = min(
                    0.95, score + doc["@search.score"] * 0.5
                )  # Blend with original score
                results.append(result)

        # Sort by score and limit to top results
        results.sort(key=lambda x: x["@search.score"], reverse=True)
        return results[:top]


# Mock the necessary modules
sys.modules["konveyor.apps.search.services.search_service"].SearchService = (
    MockSearchService
)
sys.modules["konveyor.core.conversation.factory"] = MagicMock()
sys.modules["konveyor.core.conversation.factory"].ConversationManagerFactory = (
    MockConversationManagerFactory
)

# DocumentationNavigatorSkill is imported at the top of the file


class TestDocumentationNavigatorMemory:
    """Tests for the DocumentationNavigatorSkill with conversation memory."""

    @pytest.fixture
    def skill(self):
        """Create a DocumentationNavigatorSkill instance for testing."""
        return DocumentationNavigatorSkill()

    @pytest.mark.asyncio
    async def test_create_conversation(self, skill):
        """Test creating a new conversation."""
        # Create a conversation
        conversation = await skill.create_conversation(user_id="test-user")

        # Check the conversation structure
        assert "id" in conversation
        assert conversation["user_id"] == "test-user"
        assert "created_at" in conversation

    @pytest.mark.asyncio
    async def test_answer_question_with_conversation(self, skill):
        """Test answering a question with conversation context."""
        # Create a conversation
        conversation = await skill.create_conversation(user_id="test-user")
        conversation_id = conversation["id"]

        # Answer a question
        answer = await skill.answer_question(
            question="What is the onboarding process?", conversation_id=conversation_id
        )

        # Check that the answer contains expected elements
        assert "Based on the documentation" in answer
        assert "onboarding" in answer.lower()
        assert "Sources:" in answer

        # Get the conversation manager
        conversation_manager = await skill._get_conversation_manager()

        # Check that the conversation was updated
        messages = await conversation_manager.get_conversation_messages(conversation_id)
        assert len(messages) == 2  # User question and assistant response
        assert messages[0]["type"] == "user"
        assert messages[1]["type"] == "assistant"
        assert "What is the onboarding process?" in messages[0]["content"]

    @pytest.mark.asyncio
    async def test_continue_conversation(self, skill):
        """Test continuing a conversation with follow-up questions."""
        # Create a conversation
        conversation = await skill.create_conversation(user_id="test-user")
        conversation_id = conversation["id"]

        # Answer an initial question
        await skill.answer_question(
            question="What is the onboarding process?", conversation_id=conversation_id
        )

        # Ask a follow-up question
        follow_up_answer = await skill.continue_conversation(
            follow_up_question="What should I do on my first day?",
            conversation_id=conversation_id,
        )

        # Check that the answer contains expected elements
        assert "Based on the documentation" in follow_up_answer
        assert (
            "onboarding" in follow_up_answer.lower()
            or "process" in follow_up_answer.lower()
        )
        assert "Sources:" in follow_up_answer

        # Get the conversation manager
        conversation_manager = await skill._get_conversation_manager()

        # Check that the conversation was updated
        messages = await conversation_manager.get_conversation_messages(conversation_id)
        assert len(messages) == 4  # Initial Q&A plus follow-up Q&A
        assert messages[2]["type"] == "user"
        assert messages[3]["type"] == "assistant"
        assert "What should I do on my first day?" in messages[2]["content"]

        # Ask another follow-up question
        second_follow_up_answer = await skill.continue_conversation(
            follow_up_question="Who can help me with IT setup?",
            conversation_id=conversation_id,
        )

        # Check that the answer contains expected elements
        assert "Based on the documentation" in second_follow_up_answer
        assert (
            "onboarding" in second_follow_up_answer.lower()
            or "process" in second_follow_up_answer.lower()
        )
        assert "Sources:" in second_follow_up_answer

        # Check that the conversation was updated again
        messages = await conversation_manager.get_conversation_messages(conversation_id)
        assert len(messages) == 6  # Initial Q&A plus two follow-up Q&As
        assert messages[4]["type"] == "user"
        assert messages[5]["type"] == "assistant"
        assert "Who can help me with IT setup?" in messages[4]["content"]

    @pytest.mark.asyncio
    async def test_format_for_slack_with_conversation(self, skill):
        """Test formatting search results for Slack with conversation context."""
        # Create a conversation
        conversation = await skill.create_conversation(user_id="test-user")
        conversation_id = conversation["id"]

        # Format search results for Slack
        slack_format = await skill.format_for_slack(
            query="company policies", conversation_id=conversation_id
        )

        # Check that the format contains expected elements
        assert "Search Results" in slack_format["text"]
        assert "company policies" in slack_format["text"]
        assert len(slack_format["blocks"]) > 0

        # Get the conversation manager
        conversation_manager = await skill._get_conversation_manager()

        # Check that the conversation was updated
        messages = await conversation_manager.get_conversation_messages(conversation_id)
        assert len(messages) == 2  # User query and assistant response
        assert messages[0]["type"] == "user"
        assert messages[1]["type"] == "assistant"
        assert "company policies" in messages[0]["content"]

    @pytest.mark.asyncio
    async def test_query_enhancement_with_context(self, skill):
        """Test query enhancement based on conversation context."""
        # Create a conversation
        conversation = await skill.create_conversation(user_id="test-user")
        conversation_id = conversation["id"]

        # Answer an initial question about onboarding
        await skill.answer_question(
            question="What is the onboarding process?", conversation_id=conversation_id
        )

        # Ask a follow-up question specifically about IT
        follow_up_answer = await skill.continue_conversation(
            follow_up_question="Tell me about IT setup", conversation_id=conversation_id
        )

        # The answer should contain information enhanced by the context
        assert "Based on the documentation" in follow_up_answer
        assert (
            "onboarding" in follow_up_answer.lower()
            or "process" in follow_up_answer.lower()
            or "setup" in follow_up_answer.lower()
        )
        assert "Sources:" in follow_up_answer
