"""
Response generation interface for Konveyor.

This module defines the interface for generating responses, providing a common
contract for different implementations (RAG, direct generation, etc.).
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union


class ResponseGeneratorInterface(ABC):
    """
    Interface for response generation.

    This interface defines the contract for generating responses to user queries,
    with support for different generation strategies (RAG, direct generation, etc.).
    Implementations can use different approaches while providing a consistent API.
    """

    @abstractmethod
    async def generate_response(
        self,
        query: str,
        context: Optional[str] = None,
        conversation_id: Optional[str] = None,
        use_rag: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
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

        Returns:
            Dictionary containing the response and metadata
        """
        pass

    @abstractmethod
    async def generate_with_rag(
        self,
        query: str,
        conversation_id: Optional[str] = None,
        max_context_chunks: int = 3,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate a response using RAG (Retrieval-Augmented Generation).

        This method retrieves relevant context chunks and uses them to generate
        a response to the query.

        Args:
            query: The user's query
            conversation_id: Optional conversation identifier for history
            max_context_chunks: Maximum number of context chunks to retrieve
            **kwargs: Additional generation options

        Returns:
            Dictionary containing the response and metadata
        """
        pass

    @abstractmethod
    async def generate_direct(
        self,
        query: str,
        context: Optional[str] = None,
        conversation_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate a response directly without RAG.

        This method generates a response to the query without retrieving
        additional context.

        Args:
            query: The user's query
            context: Optional context to help answer the query
            conversation_id: Optional conversation identifier for history
            **kwargs: Additional generation options

        Returns:
            Dictionary containing the response and metadata
        """
        pass

    @abstractmethod
    async def retrieve_context(
        self, query: str, max_chunks: int = 3, **kwargs
    ) -> List[Dict[str, Any]]:
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
        pass

    @abstractmethod
    def get_prompt_template(self, template_type: str) -> Dict[str, str]:
        """
        Get a prompt template for the specified type.

        This method returns a prompt template that can be used to format
        the query and context for generation.

        Args:
            template_type: Type of prompt template to get

        Returns:
            Dictionary containing the prompt template
        """
        pass

    @abstractmethod
    def format_prompt(
        self, template_type: str, context: str, query: str, **kwargs
    ) -> Dict[str, str]:
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
        pass
