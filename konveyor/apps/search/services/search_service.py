import logging
import os
import json
import time
from typing import Dict, Any, List, Optional
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchableField,
    SearchField,
    SearchFieldDataType,
    VectorSearch,
    VectorSearchProfile,
    HnswAlgorithmConfiguration,
    VectorSearchAlgorithmKind,
    VectorSearchAlgorithmMetric
)
from openai import AzureOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from django.conf import settings
from azure.core.exceptions import AzureError
from tenacity import stop_after_attempt, wait_exponential, retry_if_exception_type
from tenacity import stop_after_attempt, wait_exponential, retry_if_exception_type
from azure.storage.blob import BlobServiceClient
from azure.storage.blob import ContentSettings
import uuid
from django.utils import timezone
from .services import DocumentService
from .models import DocumentChunk

logger = logging.getLogger(__name__)

class SearchService:
    """Service for interacting with Azure Cognitive Search."""
    
    def __init__(self):
        self.search_endpoint = settings.AZURE_SEARCH_ENDPOINT
        self.search_key = settings.AZURE_SEARCH_KEY
        self.index_name = settings.AZURE_SEARCH_INDEX
        
        self.openai_client = AzureOpenAI(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION
        )
        
        # Initialize search clients
        self.search_credential = AzureKeyCredential(self.search_key)
        self.index_client = SearchIndexClient(
            endpoint=self.search_endpoint,
            credential=self.search_credential
        )
        self.search_client = SearchClient(
            endpoint=self.search_endpoint,
            index_name=self.index_name,
            credential=self.search_credential
        )
        
        # Remove duplicate blob storage initialization since we'll use DocumentService
        self.document_service = DocumentService()
    
    def create_search_index(self) -> None:
        """
        Create the search index if it doesn't exist.
        """
        if self.index_name in [index.name for index in self.index_client.list_indexes()]:
            logger.info(f"Index {self.index_name} already exists")
            return
        
        # Define vector search configuration
        vector_search = VectorSearch(
            profiles=[
                VectorSearchProfile(
                    name="embedding-profile",
                    algorithm_configuration_name="default-algorithm"
                )
            ],
            algorithms=[
                HnswAlgorithmConfiguration(
                    name="default-algorithm",
                    kind=VectorSearchAlgorithmKind.HNSW,
                    parameters={
                        "m": 4,
                        "efConstruction": 400,
                        "efSearch": 500,
                        "metric": VectorSearchAlgorithmMetric.COSINE
                    }
                )
            ]
        )
        
        # Simplified index fields - removed content_url as we use DocumentService
        fields = [
            SimpleField(name="id", type=SearchFieldDataType.String, key=True),
            SimpleField(name="document_id", type=SearchFieldDataType.String),
            SimpleField(name="chunk_index", type=SearchFieldDataType.Int32),
            SearchableField(name="content", type=SearchFieldDataType.String),
            SimpleField(name="metadata", type=SearchFieldDataType.String),
            SearchField(
                name="embedding",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                vector_search_dimensions=1536,
                vector_search_profile_name="embedding-profile"
            )
        ]
        
        index = SearchIndex(name=self.index_name, fields=fields, vector_search=vector_search)
        self.index_client.create_index(index)
        logger.info(f"Created index {self.index_name}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate an embedding for the given text using Azure OpenAI.
        Includes retry logic for resilience.
        
        Args:
            text: The text to generate an embedding for
            
        Returns:
            The embedding as a list of floats
            
        Raises:
            Exception: If embedding generation fails after retries
        """
        try:
            # Truncate text if too long (OpenAI has token limits)
            truncated_text = text[:8000]  # Adjust limit based on your needs
            
            response = self.openai_client.embeddings.create(
                model="text-embedding-ada-002",
                input=truncated_text
            )
            
            if not response.data or not response.data[0].embedding:
                raise ValueError("No embedding generated in response")
                
            return response.data[0].embedding
            
        except Exception as e:
            print(f"Error generating embedding: {str(e)}")
            raise

    def delete_index(self) -> None:
        """Delete the search index if it exists."""
        try:
            self.index_client.delete_index(self.index_name)
            logger.info(f"Search index '{self.index_name}' deleted successfully")
        except Exception as e:
            logger.error(f"Failed to delete search index: {str(e)}")
            raise
    
    def get_index(self) -> SearchIndex:
        """Get the current search index configuration."""
        try:
            return self.index_client.get_index(self.index_name)
        except Exception as e:
            logger.error(f"Failed to get search index '{self.index_name}': {str(e)}")
            raise

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=30),
        retry=retry_if_exception_type((AzureError, ConnectionError)),
        reraise=True
    )
    def index_document_chunk(
        self, 
        chunk_id: str, 
        document_id: str, 
        content: str, 
        chunk_index: int, 
        metadata: Dict[str, Any],
        embedding: List[float]
    ) -> None:
        """
        Index a document chunk in Azure Cognitive Search.
        Content should already be stored in blob storage by DocumentService.
        """
        try:
            # Simplified document preparation - no blob storage handling
            search_document = {
                "id": chunk_id,
                "document_id": document_id,
                "chunk_index": chunk_index,
                "content": content[:8000],  # Store a preview in search index
                "metadata": json.dumps(metadata),
                "embedding": embedding
            }
            
            result = self.search_client.upload_documents(documents=[search_document])
            
            if not result[0].succeeded:
                error_msg = f"Failed to index chunk {chunk_id}: {result[0].error_message}"
                logger.error(error_msg)
                raise Exception(error_msg)
                
            logger.info(f"Successfully indexed chunk {chunk_id} for document {document_id}")
            
        except Exception as e:
            logger.error(f"Error indexing document chunk {chunk_id}: {str(e)}")
            raise

    def get_chunk_content(self, chunk_id: str, document_id: str) -> str:
        """
        Retrieve chunk content using DocumentService.
        """
        return self.document_service.get_chunk_content(
            DocumentChunk.objects.get(id=chunk_id, document_id=document_id)
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(AzureError),
        reraise=True
    )
    def semantic_search(self, query: str, top: int = 5, load_full_content: bool = False) -> List[Dict[str, Any]]:
        """
        Perform semantic search using both vector embeddings and text similarity.
        """
        try:
            # Generate embedding for the query
            query_embedding = self.generate_embedding(query)
            
            # Perform hybrid search with both vector and semantic capabilities
            results = self.search_client.search(
                search_text=query,
                vector={"value": query_embedding, "fields": "embedding", "k": top},
                select=["id", "document_id", "content", "metadata", "chunk_index"],
                query_type="semantic",
                query_language="en-us",
                semantic_configuration_name="default",
                top=top
            )
            
            processed_results = []
            for result in results:
                result_data = {
                    "id": result["id"],
                    "document_id": result["document_id"],
                    "content": result["content"],
                    "metadata": json.loads(result["metadata"]),
                    "chunk_index": result["chunk_index"],
                    "score": result["@search.score"],
                    "highlights": result.get("@search.highlights", {}).get("content", []),
                    "captions": [c.text for c in result.get("@search.captions", [])]
                }
                
                if load_full_content:
                    try:
                        result_data["full_content"] = self.get_chunk_content(
                            result["id"], 
                            result["document_id"]
                        )
                    except Exception as e:
                        logger.warning(f"Could not load full content for chunk {result['id']}: {str(e)}")
                        result_data["full_content_error"] = str(e)
                
                processed_results.append(result_data)
            
            return processed_results
            
        except Exception as e:
            logger.error(f"Semantic search failed: {str(e)}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(AzureError),
        reraise=True
    )
    def vector_similarity_search(self, query: str, top: int = 5, 
                               filter_expr: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Perform pure vector similarity search.
        
        Args:
            query: Search query text
            top: Maximum number of results to return
            filter_expr: Optional OData filter expression
            
        Returns:
            List of search results with similarity scores
        """
        try:
            # Generate embedding for the query
            query_embedding = self.generate_embedding(query)
            
            # Perform vector search
            results = self.search_client.search(
                search_text=None,  # Pure vector search
                vector={"value": query_embedding, "fields": "embedding", "k": top},
                select=["id", "document_id", "content", "metadata", "chunk_index"],
                filter=filter_expr,
                top=top
            )
            
            processed_results = []
            for result in results:
                processed_results.append({
                    "id": result["id"],
                    "document_id": result["document_id"],
                    "content": result["content"],
                    "metadata": json.loads(result["metadata"]),
                    "chunk_index": result["chunk_index"],
                    "similarity_score": result["@search.score"]
                })
            
            return processed_results
            
        except Exception as e:
            logger.error(f"Vector similarity search failed: {str(e)}")
            raise 