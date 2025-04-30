"""
Views for the RAG Django app using Azure storage.

This updated version uses the new core components for conversation management,
message formatting, and response generation.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from konveyor.core.azure_utils.clients import AzureClientManager
from konveyor.core.rag.rag_service_updated import RAGService
from konveyor.core.conversation.factory import ConversationManagerFactory
from konveyor.core.formatters.factory import FormatterFactory

# Constants for message types
MESSAGE_TYPE_USER = "user"
MESSAGE_TYPE_ASSISTANT = "assistant"


class ConversationViewSet(viewsets.ViewSet):
    """
    ViewSet for managing conversations and generating responses using Azure storage.

    This updated version uses the new core components for conversation management,
    message formatting, and response generation.
    """

    def __init__(self, **kwargs):
        """Initialize the view set."""
        super().__init__(**kwargs)
        self.client_manager = AzureClientManager()
        self.rag_service = RAGService(self.client_manager)

        # Initialize the conversation manager
        self.conversation_manager = None
        self._init_conversation_manager()

        # Initialize the formatter
        self.formatter = FormatterFactory.get_formatter("markdown")

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
            # If we can't initialize the conversation manager, use the one from the RAG service
            self.conversation_manager = self.rag_service.conversation_manager

    async def create(self, request):
        """
        Create a new conversation.

        Args:
            request: The HTTP request

        Returns:
            Response containing the new conversation
        """
        user_id = str(request.user.id) if request.user.is_authenticated else None

        if self.conversation_manager:
            conversation = await self.conversation_manager.create_conversation(user_id)
            return Response(conversation)
        else:
            return Response(
                {"error": "Conversation manager not available"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    async def list(self, request):
        """
        List conversations for the current user.

        Args:
            request: The HTTP request

        Returns:
            Response containing the list of conversations
        """
        user_id = str(request.user.id) if request.user.is_authenticated else None

        if not user_id:
            return Response([])

        if self.conversation_manager:
            try:
                conversations = await self.conversation_manager.get_user_conversations(
                    user_id
                )
                return Response(conversations)
            except Exception as e:
                print(f"Error listing conversations: {str(e)}")
                return Response([])
        else:
            return Response([])

    @action(detail=True, methods=["post"])
    async def ask(self, request, pk=None):
        """
        Generate a response for a user question in a conversation.

        Request body:
        {
            "query": "user question",
            "template_type": "knowledge|code" (optional),
            "max_context_chunks": 3 (optional)
        }

        Args:
            request: The HTTP request
            pk: The conversation ID

        Returns:
            Response containing the generated response
        """
        # Validate request
        query = request.data.get("query")
        if not query:
            return Response(
                {"error": "Query is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Generate response using RAG
            response_data = await self.rag_service.generate_response(
                query=query,
                conversation_id=pk,
                template_type=request.data.get("template_type", "knowledge"),
                max_context_chunks=request.data.get("max_context_chunks", 3),
            )

            # Format the response if needed
            if self.formatter:
                try:
                    formatted_response = self.formatter.format_message(
                        response_data["answer"]
                    )
                    response_data["formatted_response"] = formatted_response
                except Exception as e:
                    print(f"Error formatting response: {str(e)}")

            return Response(
                {
                    "response": response_data["answer"],
                    "conversation_id": pk,
                    "sources": response_data.get("sources", []),
                }
            )

        except Exception as e:
            # Log error and return fallback response
            print(f"Error generating response: {e}")

            # Format error message if formatter is available
            error_message = "I apologize, but I encountered an error while processing your request. Please try again."
            formatted_error = None

            if self.formatter:
                try:
                    formatted_error = self.formatter.format_error(str(e))
                except Exception:
                    pass

            return Response(
                {
                    "error": "Failed to generate response",
                    "fallback_response": error_message,
                    "formatted_error": formatted_error,
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["get"])
    async def history(self, request, pk=None):
        """
        Get conversation history.

        Args:
            request: The HTTP request
            pk: The conversation ID

        Returns:
            Response containing the conversation history
        """
        try:
            if self.conversation_manager:
                messages = await self.conversation_manager.get_conversation_messages(
                    conversation_id=pk, limit=int(request.query_params.get("limit", 50))
                )
                return Response(messages)
            else:
                return Response(
                    {"error": "Conversation manager not available"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
        except Exception as e:
            return Response(
                {"error": f"Failed to fetch conversation history: {e}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
