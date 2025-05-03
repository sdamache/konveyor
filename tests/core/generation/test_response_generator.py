"""
Tests for the response generation components.

This module contains tests for the response generation components,
including the ResponseGenerator and ResponseGeneratorFactory.
"""

import asyncio
from typing import Any, Dict, List  # noqa: F401, F401, F401
from unittest.mock import AsyncMock, MagicMock, patch  # noqa: F401, F401, F401

import pytest

from konveyor.core.azure_utils.openai_interface import OpenAIClientInterface
from konveyor.core.generation.factory import ResponseGeneratorFactory
from konveyor.core.generation.generator import ResponseGenerator
from konveyor.core.generation.interface import ResponseGeneratorInterface


# Mock classes for testing
class MockOpenAIClient(OpenAIClientInterface):
    def generate_completion(self, messages, max_tokens=1000):
        return f"Response to: {messages[-1]['content']}"

    def generate_embedding(self, text):
        return [0.1, 0.2, 0.3]


class MockContextService:
    async def retrieve_context(self, query, max_chunks=3, **kwargs):
        return [
            {
                "content": f"Context for: {query}",
                "source": "test_source.txt",
                "relevance_score": 0.95,
            }
        ]

    def format_context(self, context_chunks):
        return "\n".join([chunk["content"] for chunk in context_chunks])


class MockConversationManager:
    async def create_conversation(self, user_id=None, metadata=None):
        return {"id": "test_conversation_id", "user_id": user_id}

    async def add_message(self, conversation_id, content, message_type, metadata=None):
        return {
            "id": "test_message_id",
            "conversation_id": conversation_id,
            "content": content,
            "type": message_type,
        }

    async def get_conversation_context(
        self, conversation_id, format="string", max_messages=None
    ):
        if format == "string":
            return "User: Test query\nAssistant: Test response"
        elif format == "dict":
            return [
                {"type": "user", "content": "Test query"},
                {"type": "assistant", "content": "Test response"},
            ]
        elif format == "openai":
            return [
                {"role": "user", "content": "Test query"},
                {"role": "assistant", "content": "Test response"},
            ]
        return ""


# Test the ResponseGenerator
@pytest.mark.asyncio()
async def test_response_generator():
    """Test the ResponseGenerator."""
    # Create mock dependencies
    openai_client = MockOpenAIClient()
    context_service = MockContextService()
    conversation_service = MockConversationManager()

    # Register our mock client with the factory
    from konveyor.core.azure_utils.openai_factory import OpenAIClientFactory

    OpenAIClientFactory.register_client("mock", openai_client)

    # Create a response generator
    generator = ResponseGenerator(
        openai_client_type="mock",
        openai_config=None,
        context_service=context_service,
        conversation_service=conversation_service,
    )

    # Replace the OpenAI client with our mock
    generator.openai_client = openai_client

    # Test generate_direct
    response_data = await generator.generate_direct(
        query="What is the capital of France?", conversation_id="test_conversation_id"
    )

    # Verify the response
    assert response_data is not None
    assert "response" in response_data
    assert "What is the capital of France?" in response_data["response"]
    assert "template_type" in response_data
    assert response_data["template_type"] == "default"
    assert "use_rag" in response_data
    assert response_data["use_rag"] is False

    # Test generate_with_rag
    rag_response_data = await generator.generate_with_rag(
        query="What is the capital of Germany?", conversation_id="test_conversation_id"
    )

    # Verify the response
    assert rag_response_data is not None
    assert "response" in rag_response_data
    assert "What is the capital of Germany?" in rag_response_data["response"]
    assert "context_chunks" in rag_response_data
    assert len(rag_response_data["context_chunks"]) == 1
    assert "template_type" in rag_response_data
    assert rag_response_data["template_type"] == "rag"
    assert "use_rag" in rag_response_data
    assert rag_response_data["use_rag"] is True

    # Test generate_response with use_rag=True
    response_data = await generator.generate_response(
        query="What is the capital of Italy?",
        conversation_id="test_conversation_id",
        use_rag=True,
    )

    # Verify the response
    assert response_data is not None
    assert "response" in response_data
    assert "What is the capital of Italy?" in response_data["response"]
    assert "context_chunks" in response_data
    assert "template_type" in response_data
    assert "use_rag" in response_data
    assert response_data["use_rag"] is True

    # Test generate_response with use_rag=False
    response_data = await generator.generate_response(
        query="What is the capital of Spain?",
        conversation_id="test_conversation_id",
        use_rag=False,
    )

    # Verify the response
    assert response_data is not None
    assert "response" in response_data
    assert "What is the capital of Spain?" in response_data["response"]
    assert "template_type" in response_data
    assert "use_rag" in response_data
    assert response_data["use_rag"] is False

    # Test retrieve_context
    context_chunks = await generator.retrieve_context(
        query="What is the capital of Japan?"
    )

    # Verify the context chunks
    assert context_chunks is not None
    assert len(context_chunks) == 1
    assert "content" in context_chunks[0]
    assert "What is the capital of Japan?" in context_chunks[0]["content"]

    # Test get_prompt_template
    template = generator.get_prompt_template("default")

    # Verify the template
    assert template is not None
    assert "system" in template
    assert "user" in template

    # Test format_prompt
    prompt = generator.format_prompt(
        template_type="default", context="Test context", query="Test query"
    )

    # Verify the prompt
    assert prompt is not None
    assert "system" in prompt
    assert "user" in prompt
    # The default template might not include the context in the system prompt
    assert "Test query" in prompt["user"]


# Test the ResponseGeneratorFactory
def test_response_generator_factory():
    """Test the ResponseGeneratorFactory."""
    # Create mock dependencies
    openai_client = MockOpenAIClient()
    context_service = MockContextService()
    conversation_service = MockConversationManager()

    # Register our mock client with the factory
    from konveyor.core.azure_utils.openai_factory import OpenAIClientFactory

    OpenAIClientFactory.register_client("mock", openai_client)

    # Create a configuration
    config = {
        "openai_client_type": "mock",
        "openai_config": None,
        "context_service": context_service,
        "conversation_service": conversation_service,
    }

    # Get a default generator
    default_generator = ResponseGeneratorFactory.get_generator("default", config)

    # Verify the generator
    assert default_generator is not None
    assert isinstance(default_generator, ResponseGeneratorInterface)
    assert isinstance(default_generator, ResponseGenerator)

    # Get a RAG generator
    rag_generator = ResponseGeneratorFactory.get_generator("rag", config)

    # Verify the generator
    assert rag_generator is not None
    assert isinstance(rag_generator, ResponseGeneratorInterface)
    assert isinstance(rag_generator, ResponseGenerator)

    # Get a chat generator
    chat_generator = ResponseGeneratorFactory.get_generator("chat", config)

    # Verify the generator
    assert chat_generator is not None
    assert isinstance(chat_generator, ResponseGeneratorInterface)
    assert isinstance(chat_generator, ResponseGenerator)

    # Test caching
    default_generator2 = ResponseGeneratorFactory.get_generator("default", config)
    assert default_generator2 is default_generator

    # Test registering a custom generator
    class CustomGenerator(ResponseGeneratorInterface):
        async def generate_response(self, query, **kwargs):
            return {"response": f"Custom response to: {query}"}

        async def generate_with_rag(self, query, **kwargs):
            return {"response": f"Custom RAG response to: {query}"}

        async def generate_direct(self, query, **kwargs):
            return {"response": f"Custom direct response to: {query}"}

        async def retrieve_context(self, query, **kwargs):
            return [{"content": f"Custom context for: {query}"}]

        def get_prompt_template(self, template_type):
            return {"system": "Custom system prompt", "user": "Custom user prompt"}

        def format_prompt(self, template_type, context, query, **kwargs):
            return {
                "system": f"Custom system prompt with {context}",
                "user": f"Custom user prompt with {query}",
            }

    custom_generator = CustomGenerator()
    ResponseGeneratorFactory.register_generator("custom", custom_generator)

    # Get the custom generator
    custom_generator2 = ResponseGeneratorFactory.get_generator("custom")
    assert custom_generator2 is custom_generator

    # Test invalid generator type
    with pytest.raises(ValueError):
        ResponseGeneratorFactory.get_generator("invalid")

    # Test invalid generator registration
    with pytest.raises(ValueError):
        ResponseGeneratorFactory.register_generator("invalid", "not a generator")


# Run the tests
if __name__ == "__main__":
    asyncio.run(test_response_generator())
    test_response_generator_factory()
