"""
Response generator for Konveyor.

This module provides a unified response generator that implements the
ResponseGeneratorInterface. It supports both RAG and direct generation approaches.
"""

import logging
import os  # noqa: F401
from typing import Any, Dict, List, Optional, Union  # noqa: F401

from konveyor.core.azure_utils.openai_factory import OpenAIClientFactory
from konveyor.core.generation.interface import ResponseGeneratorInterface

logger = logging.getLogger(__name__)


class ResponseGenerator(ResponseGeneratorInterface):
    """
    Unified response generator.

    This class implements the ResponseGeneratorInterface and provides a unified
    approach to generating responses. It supports both RAG and direct generation
    approaches.
    """

    def __init__(
        self,
        openai_client_type: str = "unified",
        openai_config: dict[str, Any] | None = None,
        context_service=None,
        conversation_service=None,
    ):
        """
        Initialize the response generator.

        Args:
            openai_client_type: Type of OpenAI client to use ('unified', 'custom', 'sdk')  # noqa: E501
            openai_config: Configuration for the OpenAI client
            context_service: Service for retrieving context (for RAG)
            conversation_service: Service for managing conversations
        """
        # Initialize the OpenAI client
        self.openai_client = OpenAIClientFactory.get_client(
            client_type=openai_client_type, config=openai_config
        )

        # Store the context and conversation services
        self.context_service = context_service
        self.conversation_service = conversation_service

        # Initialize prompt templates
        self.prompt_templates = {
            "default": {"system": "You are a helpful assistant.", "user": "{query}"},
            "rag": {
                "system": "You are a helpful assistant. Use the following context to answer the question. If the context doesn't contain the answer, say so.\n\nContext:\n{context}",  # noqa: E501
                "user": "{query}",
            },
            "chat": {
                "system": "You are a helpful assistant. Provide a friendly and informative response.",  # noqa: E501
                "user": "{query}",
            },
        }

        logger.info("Initialized ResponseGenerator")

    async def generate_response(
        self,
        query: str,
        context: str | None = None,
        conversation_id: str | None = None,
        use_rag: bool = False,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Generate a response for the given query.

        This is the main entry point for response generation. It can use either
        RAG or direct generation based on the use_rag parameter.

        Args:
            query: The user's query
            context: Optional context to help answer the query
            conversation_id: Optional conversation identifier for history
            use_rag: Whether to use RAG for context retrieval
            **kwargs: Additional generation options
                - template_type: Type of prompt template to use
                - max_tokens: Maximum number of tokens to generate
                - temperature: Sampling temperature

        Returns:
            Dictionary containing the response and metadata
        """
        if use_rag:
            return await self.generate_with_rag(
                query=query, conversation_id=conversation_id, **kwargs
            )
        else:
            return await self.generate_direct(
                query=query, context=context, conversation_id=conversation_id, **kwargs
            )

    async def generate_with_rag(
        self,
        query: str,
        conversation_id: str | None = None,
        max_context_chunks: int = 3,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Generate a response using RAG (Retrieval-Augmented Generation).

        This method retrieves relevant context chunks and uses them to generate
        a response to the query.

        Args:
            query: The user's query
            conversation_id: Optional conversation identifier for history
            max_context_chunks: Maximum number of context chunks to retrieve
            **kwargs: Additional generation options
                - template_type: Type of prompt template to use
                - max_tokens: Maximum number of tokens to generate
                - temperature: Sampling temperature

        Returns:
            Dictionary containing the response and metadata
        """
        # Check if context service is available
        if not self.context_service:
            logger.warning(
                "Context service not available, falling back to direct generation"
            )
            return await self.generate_direct(
                query=query, conversation_id=conversation_id, **kwargs
            )

        # Get template type
        template_type = kwargs.get("template_type", "rag")

        try:
            # Retrieve relevant context chunks
            context_chunks = await self.retrieve_context(
                query=query, max_chunks=max_context_chunks
            )

            # Format context into a string
            formatted_context = self._format_context_chunks(context_chunks)

            # Format prompt
            prompt = self.format_prompt(
                template_type=template_type, context=formatted_context, query=query
            )

            # Generate response
            max_tokens = kwargs.get("max_tokens", 1000)
            messages = [
                {"role": "system", "content": prompt["system"]},
                {"role": "user", "content": prompt["user"]},
            ]

            response_text = self.openai_client.generate_completion(
                messages=messages, max_tokens=max_tokens
            )

            # Store in conversation history if available
            if self.conversation_service and conversation_id:
                await self._update_conversation_history(
                    conversation_id=conversation_id, query=query, response=response_text
                )

            # Return response with metadata
            return {
                "response": response_text,
                "context_chunks": context_chunks,
                "template_type": template_type,
                "use_rag": True,
            }

        except Exception as e:
            logger.error(f"Error generating response with RAG: {str(e)}")
            # Fall back to direct generation
            logger.info("Falling back to direct generation")
            return await self.generate_direct(
                query=query, conversation_id=conversation_id, **kwargs
            )

    async def generate_direct(
        self,
        query: str,
        context: str | None = None,
        conversation_id: str | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Generate a response directly without RAG.

        This method generates a response to the query without retrieving
        additional context.

        Args:
            query: The user's query
            context: Optional context to help answer the query
            conversation_id: Optional conversation identifier for history
            **kwargs: Additional generation options
                - template_type: Type of prompt template to use
                - max_tokens: Maximum number of tokens to generate
                - temperature: Sampling temperature

        Returns:
            Dictionary containing the response and metadata
        """
        # Get template type
        template_type = kwargs.get("template_type", "default")

        try:
            # Format prompt
            prompt = self.format_prompt(
                template_type=template_type, context=context or "", query=query
            )

            # Generate response
            max_tokens = kwargs.get("max_tokens", 1000)
            messages = [
                {"role": "system", "content": prompt["system"]},
                {"role": "user", "content": prompt["user"]},
            ]

            response_text = self.openai_client.generate_completion(
                messages=messages, max_tokens=max_tokens
            )

            # Store in conversation history if available
            if self.conversation_service and conversation_id:
                await self._update_conversation_history(
                    conversation_id=conversation_id, query=query, response=response_text
                )

            # Return response with metadata
            return {
                "response": response_text,
                "template_type": template_type,
                "use_rag": False,
            }

        except Exception as e:
            logger.error(f"Error generating direct response: {str(e)}")
            raise

    async def retrieve_context(
        self, query: str, max_chunks: int = 3, **kwargs
    ) -> list[dict[str, Any]]:
        """
        Retrieve relevant context chunks for a query.

        This method retrieves context chunks that are relevant to the query,
        which can be used for RAG.

        Args:
            query: The user's query
            max_chunks: Maximum number of context chunks to retrieve
            **kwargs: Additional retrieval options

        Returns:
            List of context chunk dictionaries
        """
        # Check if context service is available
        if not self.context_service:
            logger.warning("Context service not available")
            return []

        try:
            # Retrieve context chunks
            context_chunks = await self.context_service.retrieve_context(
                query=query, max_chunks=max_chunks, **kwargs
            )

            return context_chunks

        except Exception as e:
            logger.error(f"Error retrieving context: {str(e)}")
            return []

    def get_prompt_template(self, template_type: str) -> dict[str, str]:
        """
        Get a prompt template for the specified type.

        This method returns a prompt template that can be used to format
        the query and context for generation.

        Args:
            template_type: Type of prompt template to get

        Returns:
            Dictionary containing the prompt template
        """
        if template_type in self.prompt_templates:
            return self.prompt_templates[template_type]
        else:
            logger.warning(f"Template type '{template_type}' not found, using default")
            return self.prompt_templates["default"]

    def format_prompt(
        self, template_type: str, context: str, query: str, **kwargs
    ) -> dict[str, str]:
        """
        Format a prompt using the specified template.

        This method formats the query and context using the specified
        prompt template.

        Args:
            template_type: Type of prompt template to use
            context: Context to include in the prompt
            query: Query to include in the prompt
            **kwargs: Additional formatting options

        Returns:
            Dictionary containing the formatted prompt
        """
        # Get the template
        template = self.get_prompt_template(template_type)

        # Format the template
        formatted_prompt = {
            "system": template["system"].format(context=context, query=query, **kwargs),
            "user": template["user"].format(context=context, query=query, **kwargs),
        }

        return formatted_prompt

    def _format_context_chunks(self, context_chunks: list[dict[str, Any]]) -> str:
        """
        Format context chunks into a string.

        Args:
            context_chunks: List of context chunk dictionaries

        Returns:
            Formatted context string
        """
        if not context_chunks:
            return ""

        formatted_context = ""

        for i, chunk in enumerate(context_chunks, 1):
            content = chunk.get("content", "")
            source = chunk.get("source", "")

            formatted_context += f"[{i}] {content}\n"
            if source:
                formatted_context += f"Source: {source}\n"
            formatted_context += "\n"

        return formatted_context.strip()

    async def _update_conversation_history(
        self, conversation_id: str, query: str, response: str
    ) -> None:
        """
        Update the conversation history.

        Args:
            conversation_id: Conversation identifier
            query: User query
            response: Assistant response
        """
        if not self.conversation_service:
            return

        try:
            # Add user message
            await self.conversation_service.add_message(
                conversation_id=conversation_id, content=query, message_type="user"
            )

            # Add assistant message
            await self.conversation_service.add_message(
                conversation_id=conversation_id,
                content=response,
                message_type="assistant",
            )

        except Exception as e:
            logger.error(f"Error updating conversation history: {str(e)}")
