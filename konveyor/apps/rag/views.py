"""
Views for the RAG Django app using Azure storage.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from konveyor.core.azure.client_manager import AzureClientManager
from konveyor.services.rag.rag_service import RAGService
from .models import ConversationManager, MESSAGE_TYPE_USER, MESSAGE_TYPE_ASSISTANT

class ConversationViewSet(viewsets.ViewSet):
    """ViewSet for managing conversations and generating responses using Azure storage."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.client_manager = AzureClientManager()
        self.rag_service = RAGService(self.client_manager)
        self.conversation_manager = ConversationManager()
    
    async def create(self, request):
        """Create a new conversation."""
        user_id = str(request.user.id) if request.user.is_authenticated else None
        conversation = await self.conversation_manager.create_conversation(user_id)
        return Response(conversation)
    
    async def list(self, request):
        """List conversations for the current user."""
        # This would need to be implemented in storage.py to filter by user
        return Response([])
    
    @action(detail=True, methods=['post'])
    async def ask(self, request, pk=None):
        """
        Generate a response for a user question in a conversation.
        
        Request body:
        {
            "query": "user question",
            "template_type": "knowledge|code" (optional),
            "max_context_chunks": 3 (optional)
        }
        """
        # Validate request
        query = request.data.get('query')
        if not query:
            return Response(
                {'error': 'Query is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Save user message
            user_message = await self.conversation_manager.add_message(
                conversation_id=pk,
                content=query,
                message_type=MESSAGE_TYPE_USER
            )
            
            # Generate response using RAG
            response_data = await self.rag_service.generate_response(
                query=query,
                template_type=request.data.get('template_type', 'knowledge'),
                max_context_chunks=request.data.get('max_context_chunks', 3)
            )
            
            # Save assistant message with metadata
            assistant_message = await self.conversation_manager.add_message(
                conversation_id=pk,
                content=response_data['response'],
                message_type=MESSAGE_TYPE_ASSISTANT,
                metadata={
                    'context_chunks': response_data['context_chunks'],
                    'prompt_template': response_data['prompt_template']
                }
            )
            
            return Response({
                'response': response_data['response'],
                'message_id': assistant_message['id'],
                'conversation_id': pk
            })
            
        except Exception as e:
            # Log error and return fallback response
            print(f"Error generating response: {e}")
            return Response(
                {
                    'error': 'Failed to generate response',
                    'fallback_response': 'I apologize, but I encountered an error while processing your request. Please try again.'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    async def history(self, request, pk=None):
        """Get conversation history."""
        try:
            messages = await self.conversation_manager.get_conversation_messages(
                conversation_id=pk,
                limit=int(request.query_params.get('limit', 50))
            )
            return Response(messages)
        except Exception as e:
            return Response(
                {'error': f'Failed to fetch conversation history: {e}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
