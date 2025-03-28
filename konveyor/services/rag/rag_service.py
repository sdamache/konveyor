"""
RAG service implementation for Konveyor.
Handles high-level RAG operations including context retrieval and response generation.
"""
import os
from typing import List, Dict, Optional
from konveyor.core.azure.rag_templates import RAGPromptManager
from konveyor.core.azure.clients import AzureClientManager
from .context_service import ContextService

class RAGService:
    """Main service for RAG operations."""
    
    def __init__(self, client_manager: AzureClientManager):
        self.client_manager = client_manager
        self.prompt_manager = RAGPromptManager()
        self.context_service = ContextService(client_manager)
        self.openai_client = self.client_manager.get_openai_client()
    
    async def generate_response(
        self,
        query: str,
        conversation_id: Optional[str] = None,
        template_type: str = "knowledge",
        max_context_chunks: int = 3,
        temperature: float = 0.7
    ) -> Dict[str, any]:
        """
        Generate a response using RAG pipeline.
        
        Args:
            query: User's question
            template_type: Type of prompt template to use
            max_context_chunks: Maximum number of context chunks to retrieve
            temperature: OpenAI temperature parameter
            
        Returns:
            Dictionary containing response and metadata
        """
        # Retrieve relevant context
        context_chunks = await self.context_service.retrieve_context(
            query=query,
            max_chunks=max_context_chunks
        )
        
        # Format context into prompt
        formatted_context = self.context_service.format_context(context_chunks)
        
        # Get and format prompt template
        prompt = self.prompt_manager.format_prompt(
            template_type,
            context=formatted_context,
            query=query
        )
        
        # Generate response using Azure OpenAI
        completion = self.openai_client.chat.completions.create(
            model=os.environ.get('AZURE_OPENAI_CHAT_DEPLOYMENT', 'gpt-deployment'),
            messages=[
                {"role": "system", "content": prompt["system"]},
                {"role": "user", "content": prompt["user"]}
            ],
            temperature=temperature
        )
        
        # Extract sources from context chunks
        sources = [{
            "source": chunk["source"],
            "page": chunk.get("page"),
            "relevance_score": chunk["relevance_score"]
        } for chunk in context_chunks]
        
        # Store conversation messages if conversation_id provided
        if conversation_id:
            storage_manager = self.client_manager.get_storage_manager()
            
            # Store user query
            await storage_manager.add_message(
                conversation_id=conversation_id,
                message_type="user",
                content=query
            )
            
            # Store assistant response
            await storage_manager.add_message(
                conversation_id=conversation_id,
                message_type="assistant",
                content=completion.choices[0].message.content,
                metadata={
                    "context_chunks": [{
                        "source": chunk["source"],
                        "content": chunk["content"]
                    } for chunk in context_chunks],
                    "prompt_template": template_type
                }
            )
        
        return {
            "answer": completion.choices[0].message.content,
            "sources": sources
        }
