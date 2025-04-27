"""
Tests for the conversation management components.

This module contains tests for the conversation management components,
including the InMemoryConversationManager and the ConversationManagerFactory.
"""

import os
import pytest
import asyncio
from typing import Dict, Any, List

from konveyor.core.conversation.interface import ConversationInterface
from konveyor.core.conversation.memory import InMemoryConversationManager
from konveyor.core.conversation.factory import ConversationManagerFactory

# Test the InMemoryConversationManager
@pytest.mark.asyncio
async def test_in_memory_conversation_manager():
    """Test the InMemoryConversationManager."""
    # Create a conversation manager
    manager = InMemoryConversationManager()
    
    # Create a conversation
    conversation = await manager.create_conversation(user_id="test_user")
    
    # Verify the conversation was created
    assert conversation is not None
    assert "id" in conversation
    assert conversation["user_id"] == "test_user"
    
    # Add a message to the conversation
    message = await manager.add_message(
        conversation_id=conversation["id"],
        content="Hello, world!",
        message_type="user"
    )
    
    # Verify the message was added
    assert message is not None
    assert "id" in message
    assert message["conversation_id"] == conversation["id"]
    assert message["content"] == "Hello, world!"
    assert message["type"] == "user"
    
    # Get the conversation messages
    messages = await manager.get_conversation_messages(conversation["id"])
    
    # Verify the messages were retrieved
    assert messages is not None
    assert len(messages) == 1
    assert messages[0]["content"] == "Hello, world!"
    
    # Get the conversation context
    context = await manager.get_conversation_context(conversation["id"])
    
    # Verify the context was retrieved
    assert context is not None
    assert "User: Hello, world!" in context
    
    # Add an assistant message
    assistant_message = await manager.add_message(
        conversation_id=conversation["id"],
        content="How can I help you?",
        message_type="assistant"
    )
    
    # Verify the message was added
    assert assistant_message is not None
    assert assistant_message["content"] == "How can I help you?"
    
    # Get the conversation context in different formats
    string_context = await manager.get_conversation_context(conversation["id"], format="string")
    dict_context = await manager.get_conversation_context(conversation["id"], format="dict")
    openai_context = await manager.get_conversation_context(conversation["id"], format="openai")
    
    # Verify the contexts were retrieved in the correct format
    assert "User: Hello, world!" in string_context
    assert "Assistant: How can I help you?" in string_context
    
    assert len(dict_context) == 2
    assert dict_context[0]["content"] == "Hello, world!"
    assert dict_context[1]["content"] == "How can I help you?"
    
    assert len(openai_context) == 2
    assert openai_context[0]["role"] == "user"
    assert openai_context[0]["content"] == "Hello, world!"
    assert openai_context[1]["role"] == "assistant"
    assert openai_context[1]["content"] == "How can I help you?"
    
    # Update the conversation metadata
    updated_conversation = await manager.update_conversation_metadata(
        conversation_id=conversation["id"],
        metadata={"test_key": "test_value"}
    )
    
    # Verify the metadata was updated
    assert updated_conversation is not None
    assert "metadata" in updated_conversation
    assert updated_conversation["metadata"]["test_key"] == "test_value"
    
    # Get user conversations
    user_conversations = await manager.get_user_conversations("test_user")
    
    # Verify the user conversations were retrieved
    assert user_conversations is not None
    assert len(user_conversations) == 1
    assert user_conversations[0]["id"] == conversation["id"]
    
    # Delete the conversation
    result = await manager.delete_conversation(conversation["id"])
    
    # Verify the conversation was deleted
    assert result is True
    
    # Try to get the deleted conversation's messages
    deleted_messages = await manager.get_conversation_messages(conversation["id"])
    
    # Verify no messages were retrieved
    assert deleted_messages is not None
    assert len(deleted_messages) == 0

# Test the ConversationManagerFactory
@pytest.mark.asyncio
async def test_conversation_manager_factory():
    """Test the ConversationManagerFactory."""
    # Create a memory conversation manager
    memory_manager = await ConversationManagerFactory.create_manager("memory")
    
    # Verify the manager was created
    assert memory_manager is not None
    assert isinstance(memory_manager, ConversationInterface)
    assert isinstance(memory_manager, InMemoryConversationManager)
    
    # Test the manager
    conversation = await memory_manager.create_conversation(user_id="test_user")
    assert conversation is not None
    assert "id" in conversation
    
    # Get the default storage type
    storage_type = ConversationManagerFactory.get_default_storage_type()
    
    # Verify the storage type
    assert storage_type in ["memory", "azure"]

# Run the tests
if __name__ == "__main__":
    asyncio.run(test_in_memory_conversation_manager())
    asyncio.run(test_conversation_manager_factory())
