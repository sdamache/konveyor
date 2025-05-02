"""
RAG service implementation for Konveyor.
Handles high-level RAG operations including context retrieval and response generation.

This updated version uses the new core components for conversation management,
message formatting, and response generation.
"""

import os
from typing import Any, Dict, List, Optional  # noqa: F401

from konveyor.core.azure_utils.clients import AzureClientManager
from konveyor.core.conversation.factory import ConversationManagerFactory
from konveyor.core.formatters.factory import FormatterFactory
from konveyor.core.generation.factory import ResponseGeneratorFactory
from konveyor.core.rag.context_service import ContextService


class RAGService:
    """
    Main service for RAG operations.

    This updated version uses the new core components for conversation management,
    message formatting, and response generation.
    """

    def __init__(self, client_manager: AzureClientManager):
        """
        Initialize the RAG service.

        Args:
            client_manager: Azure client manager for accessing Azure services
        """
        self.client_manager = client_manager
        self.context_service = ContextService(client_manager)

        # Initialize the conversation manager
        self.conversation_manager = None
        self._init_conversation_manager()

        # Initialize the formatter
        self.formatter = FormatterFactory.get_formatter("markdown")

        # Initialize the response generator
        self.response_generator = None
        self._init_response_generator()

    async def _init_conversation_manager(self):
        """Initialize the conversation manager."""
        try:
            # Try to use Azure storage first, fall back to in-memory if not available
            try:
                self.conversation_manager = (
                    await ConversationManagerFactory.create_manager("azure")
                )
            except Exception:
                self.conversation_manager = (
                    await ConversationManagerFactory.create_manager("memory")
                )
        except Exception as e:
            print(f"Failed to initialize conversation manager: {str(e)}")

    def _init_response_generator(self):
        """Initialize the response generator."""
        try:
            # Configure the response generator with the conversation manager and context service  # noqa: E501
            config = {
                "conversation_service": self.conversation_manager,
                "context_service": self.context_service,
            }
            self.response_generator = ResponseGeneratorFactory.get_generator(
                "rag", config
            )
        except Exception as e:
            print(f"Failed to initialize response generator: {str(e)}")

    async def generate_response(
        self,
        query: str,
        conversation_id: Optional[str] = None,
        template_type: str = "knowledge",
        max_context_chunks: int = 3,
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        """
        Generate a response using RAG pipeline.

        Args:
            query: User's question
            conversation_id: Optional conversation identifier
            template_type: Type of prompt template to use
            max_context_chunks: Maximum number of context chunks to retrieve
            temperature: OpenAI temperature parameter

        Returns:
            Dictionary containing response and metadata
        """
        # Use the response generator if available
        if self.response_generator:
            try:
                # Generate the response using the response generator
                response_data = await self.response_generator.generate_response(
                    query=query,
                    conversation_id=conversation_id,
                    use_rag=True,
                    template_type=template_type,
                    max_context_chunks=max_context_chunks,
                )

                # Extract sources from context chunks
                sources = []
                if "context_chunks" in response_data:
                    sources = [
                        {
                            "source": chunk.get("source", ""),
                            "page": chunk.get("page"),
                            "relevance_score": chunk.get("relevance_score", 0),
                        }
                        for chunk in response_data.get("context_chunks", [])
                    ]

                return {
                    "answer": response_data.get("response", ""),
                    "sources": sources,
                    "context_chunks": response_data.get("context_chunks", []),
                    "prompt_template": template_type,
                }
            except Exception as e:
                print(f"Error using response generator: {str(e)}")
                # Fall back to the original implementation

        # Fall back to the original implementation
        print(
            "Response generator not available, falling back to original implementation"
        )

        # Retrieve relevant context
        context_chunks = await self.context_service.retrieve_context(
            query=query, max_chunks=max_context_chunks
        )

        # Format context into prompt
        formatted_context = self.context_service.format_context(context_chunks)

        # Get and format prompt template
        from konveyor.core.rag.templates import RAGPromptManager

        prompt_manager = RAGPromptManager()
        prompt = prompt_manager.format_prompt(
            template_type, context=formatted_context, query=query
        )

        # Generate response using Azure OpenAI
        openai_client = self.client_manager.get_openai_client()
        completion = openai_client.chat.completions.create(
            model=os.environ.get("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-deployment"),
            messages=[
                {"role": "system", "content": prompt["system"]},
                {"role": "user", "content": prompt["user"]},
            ],
            temperature=temperature,
        )

        # Extract sources from context chunks
        sources = [
            {
                "source": chunk["source"],
                "page": chunk.get("page"),
                "relevance_score": chunk["relevance_score"],
            }
            for chunk in context_chunks
        ]

        # Store conversation messages if conversation_id provided
        if conversation_id and self.conversation_manager:
            try:
                # Store user query
                await self.conversation_manager.add_message(
                    conversation_id=conversation_id, content=query, message_type="user"
                )

                # Store assistant response
                await self.conversation_manager.add_message(
                    conversation_id=conversation_id,
                    content=completion.choices[0].message.content,
                    message_type="assistant",
                    metadata={
                        "context_chunks": [
                            {"source": chunk["source"], "content": chunk["content"]}
                            for chunk in context_chunks
                        ],
                        "prompt_template": template_type,
                    },
                )
            except Exception as e:
                print(f"Error storing conversation messages: {str(e)}")

        return {
            "answer": completion.choices[0].message.content,
            "sources": sources,
            "context_chunks": context_chunks,
            "prompt_template": template_type,
        }
