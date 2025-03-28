"""Azure Cognitive Search service.

This module provides functionality for document search using Azure Cognitive Search,
including vector search with OpenAI embeddings and hybrid search capabilities.

Example:
    ```python
    # Initialize service
    search = SearchService()
    
    # Perform hybrid search
    results = search.hybrid_search(
        query="machine learning",
        top=5,
        load_full_content=True
    )
    ```
"""

import logging
import os
import json
import time
from typing import Dict, Any, List, Optional, Tuple

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
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
    VectorSearchAlgorithmMetric,
    VectorSearchAlgorithmConfiguration
)
from openai import AzureOpenAI
from django.conf import settings
from azure.core.exceptions import AzureError
from azure.storage.blob import BlobServiceClient
from django.utils import timezone

from konveyor.core.azure.service import AzureService
from konveyor.services.documents.document_service import DocumentService
from konveyor.apps.documents.models import DocumentChunk
from konveyor.core.azure.retry import azure_retry
from konveyor.core.azure.mixins import ServiceLoggingMixin, AzureClientMixin, AzureServiceConfig

logger = logging.getLogger(__name__)

class SearchService(AzureService):
    """Service for interacting with Azure Cognitive Search."""
    
    def __init__(self):
        """Initialize search service with Azure clients and configuration.
        
        Sets up Azure Search and OpenAI clients, creates search index if needed,
        and initializes document processing service.
        
        Raises:
            Exception: If client initialization fails
        """
        # Initialize base class
        super().__init__('SEARCH')
        self.log_init("SearchService")
        
        # Get configuration
        self.index_name = os.getenv('AZURE_SEARCH_INDEX_NAME', 'konveyor-documents')
        self.log_success(f"Search index name: {self.index_name}")
        
        # Get OpenAI configuration
        openai_version = os.getenv('AZURE_OPENAI_API_VERSION', '2024-12-01-preview')
        embedding_deployment = os.getenv('AZURE_OPENAI_EMBEDDING_DEPLOYMENT', 'embeddings')
        self.log_success(f"OpenAI API version: {openai_version}")
        self.log_success(f"OpenAI embedding deployment: {embedding_deployment}")
        
        try:
            # Initialize search clients
            self.index_client, self.search_client = self.client_manager.get_search_clients(self.index_name)
            
            # Test index client
            indexes = list(self.index_client.list_indexes())
            index_names = [index.name for index in indexes]
            self.log_success(f"Found {len(indexes)} indexes: {', '.join(index_names)}")
            
            # Initialize OpenAI client
            self.openai_client = self.client_manager.get_openai_client()
            
            # Test embedding generation
            test_embedding = self.generate_embedding("test")
            self.log_success(f"Test embedding generation successful: {len(test_embedding)} dimensions")
            
            # Initialize document service
            self.document_service = DocumentService()
            self.log_success("Successfully initialized DocumentService")
            
            self.log_success("SearchService initialization completed successfully")
            
        except Exception as e:
            self.log_error("Failed to initialize service", e)
            raise
    
    def create_search_index(self, index_name=None):
        """
        Create the search index if it doesn't exist, with detailed logging.
        """
        logger.info("Creating search index...")
        
        # Use provided index_name or fall back to settings
        index_name = index_name or self.index_name
        logger.info(f"Using index name: {index_name}")
        
        # Check if index already exists
        try:
            existing_indices = [index.name for index in self.index_client.list_indexes()]
            if index_name in existing_indices:
                logger.info(f"Index {index_name} already exists, skipping creation")
                return True
            logger.info(f"Index {index_name} does not exist, will create")
        except Exception as e:
            logger.warning(f"Could not check if index exists: {e}")
        
        logger.info("Defining vector search algorithm configuration...")
        try:
            # Define vector search algorithm with explicit parameters to avoid SDK version issues
            algorithm_config = {
                "name": "default-algorithm-config",
                "kind": "hnsw",  # Explicitly set kind as a string
                "hnsw_parameters": {
                    "m": 4,
                    "efConstruction": 400,
                    "efSearch": 500,
                    "metric": "cosine"
                }
            }
            
            logger.info(f"Created algorithm config: {algorithm_config['name']}, kind: {algorithm_config['kind']}")
            
            # Create vector search configuration with profiles
            vector_search = {
                "algorithms": [algorithm_config],
                "profiles": [
                    {
                        "name": "embedding-profile",
                        "algorithm_configuration_name": "default-algorithm-config",
                        "algorithm": "default-algorithm-config",
                        "vector_fields": ["embedding"]
                    }
                ]
            }
            
            logger.info(f"Created vector search profile: embedding-profile, algorithm: default-algorithm-config")
            
        except Exception as e:
            logger.error(f"Failed to create vector search configuration: {e}")
            raise
        
        logger.info("Defining index fields...")
        try:
            # Create the index definition with all necessary configuration
            index_definition = {
                "name": index_name,
                "fields": [
                    {
                        "name": "id",
                        "type": "Edm.String",
                        "key": True,
                        "searchable": False,
                        "filterable": True,
                        "sortable": True
                    },
                    {
                        "name": "chunk_id",
                        "type": "Edm.String",
                        "searchable": False,
                        "filterable": True,
                        "sortable": False
                    },
                    {
                        "name": "document_id",
                        "type": "Edm.String",
                        "searchable": False,
                        "filterable": True,
                        "sortable": False
                    },
                    {
                        "name": "chunk_index",
                        "type": "Edm.Int32",
                        "searchable": False,
                        "filterable": True,
                        "sortable": True
                    },
                    {
                        "name": "content",
                        "type": "Edm.String",
                        "searchable": True,
                        "filterable": False,
                        "sortable": False,
                        "analyzer_name": "standard.lucene"
                    },
                    {
                        "name": "metadata",
                        "type": "Edm.String",
                        "searchable": False,
                        "filterable": False,
                        "sortable": False
                    },
                    {
                        "name": "embedding",
                        "type": "Collection(Edm.Single)",
                        "searchable": True,
                        "filterable": False,
                        "sortable": False,
                        "retrievable": False,
                        "stored": False,
                        "dimensions": 1536,
                        "vectorSearchProfile": "embedding-profile",
                        "nullable": True  # Allow null values for embedding field
                    }
                ],
                "vectorSearch": vector_search
            }
            
            # Try to create index using different methods
            logger.info(f"Creating index {index_name} in Azure...")
            try:
                # First try using create_or_update_index with dictionary
                self.index_client.create_or_update_index(index_definition)
                logger.info(f"Successfully created index {index_name} using dictionary approach")
            except Exception as e1:
                logger.warning(f"Dictionary-based index creation failed: {e1}")
                try:
                    # Try with SearchIndex object if dictionary approach failed
                    from azure.search.documents.indexes.models import SearchIndex
                    index = SearchIndex.deserialize(index_definition)
                    self.index_client.create_index(index)
                    logger.info(f"Successfully created index {index_name} using SearchIndex object")
                except Exception as e2:
                    logger.error(f"Both index creation methods failed. Last error: {e2}")
                    # Check if index was created despite errors
                    try:
                        existing_indices = [index.name for index in self.index_client.list_indexes()]
                        if index_name in existing_indices:
                            logger.info(f"Index {index_name} exists despite errors, proceeding")
                            return True
                    except Exception:
                        pass
                    raise e2
            
            # Update the search client to use the new index
            # Get the endpoint and key from environment variables
            endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
            api_key = os.getenv('AZURE_SEARCH_API_KEY')
            
            # Create AzureKeyCredential
            from azure.core.credentials import AzureKeyCredential
            credential = AzureKeyCredential(api_key)
            
            # Create a new search client with the new index
            self.search_client = SearchClient(
                endpoint=endpoint,
                index_name=index_name,
                credential=credential
            )
            logger.info(f"Updated search client to use index: {index_name}")
            
            return True
        except Exception as e:
            logger.error(f"Failed to create index {index_name}: {e}")
            if "vectorSearch.algorithms[0].kind" in str(e):
                logger.error("The 'kind' field is required but was not properly set. Check your SDK version compatibility.")
            raise

    @azure_retry()
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate an embedding for the given text using LangChain's AzureOpenAIEmbeddings.
        Includes retry logic for resilience and detailed logging.
        
        Args:
            text: The text to generate an embedding for
            
        Returns:
            The embedding as a list of floats
            
        Raises:
            Exception: If embedding generation fails after retries
        """
        self.log_success(f"Generating embedding for text ({len(text)} chars)...")
        
        if self.openai_client:
            # Use Azure OpenAI client
            try:
                # Get deployment name from environment variable
                embedding_deployment = os.getenv('AZURE_OPENAI_EMBEDDING_DEPLOYMENT', 'text-embedding-ada-002')
                self.log_success(f"Using embedding deployment: {embedding_deployment}")
                
                response = self.openai_client.embeddings.create(
                    model=embedding_deployment,
                    input=text
                )
                return response.data[0].embedding
            except Exception as e:
                self.log_error("Failed to generate embedding with Azure OpenAI client", e)
                raise
        
        if not self.openai_client:
            error_msg = "Azure OpenAI client not configured correctly"
            self.log_error(error_msg)
            raise ValueError(error_msg)
        
        try:
            # Truncate text if too long (OpenAI has token limits)
            truncated_text = text[:8000]  # Adjust limit based on your needs
            if len(truncated_text) < len(text):
                logger.info(f"Truncated text from {len(text)} to {len(truncated_text)} chars")
            
            # Get deployment name
            embedding_deployment = os.getenv('AZURE_OPENAI_EMBEDDING_DEPLOYMENT', 'text-embedding-ada-002')
            
            # Generate embedding
            response = self.openai_client.embeddings.create(
                model=embedding_deployment,
                input=truncated_text
            )
            embedding = response.data[0].embedding
            self.log_success(f"Generated embedding with {len(embedding)} dimensions")
            return embedding
            
        except Exception as e:
            error_msg = f"Error generating embedding: {str(e)}"
            self.log_error(error_msg)
            raise
            
            # Additional diagnostic info
            if "404" in str(e):
                logger.error("404 error indicates the resource was not found. Check:")
                logger.error("1. OpenAI endpoint URL is correct")
                logger.error("2. API key is valid and has access to the embeddings model")
                logger.error("3. The model name is correct (should match your Azure OpenAI deployment name)")
                logger.error("4. The model is deployed to your OpenAI resource")
                logger.error(f"Current model: {os.getenv('AZURE_OPENAI_EMBEDDING_DEPLOYMENT', 'text-embedding-ada-002')}")
            
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
        embedding: Optional[List[float]] = None
    ) -> bool:
        """
        Index a document chunk in Azure Cognitive Search.
        Content should already be stored in blob storage by DocumentService.
        
        Args:
            chunk_id: Unique identifier for the chunk
            document_id: ID of the parent document
            content: Text content to index
            chunk_index: Index of this chunk within the document
            metadata: Additional metadata to store
            embedding: Optional pre-computed embedding. If None, will be generated from content.
        
        Returns:
            bool: True if indexing was successful
        """
        try:
            # Generate embedding if not provided
            if embedding is None and content:
                try:
                    embedding = self.generate_embedding(content)
                except Exception as e:
                    logger.warning(f"Failed to generate embedding for chunk {chunk_id}: {e}")
                    embedding = None
            
            # Prepare document for indexing
            search_document = {
                "id": chunk_id,
                "document_id": document_id,
                "chunk_index": chunk_index,
                "content": content[:8000],  # Store a preview in search index
                "metadata": json.dumps(metadata)
            }
            
            # Only include embedding if we have one
            if embedding is not None:
                search_document["embedding"] = embedding
            
            result = self.search_client.upload_documents(documents=[search_document])
            
            if not result[0].succeeded:
                error_msg = f"Failed to index chunk {chunk_id}: {result[0].error_message}"
                logger.error(error_msg)
                raise Exception(error_msg)
                
            logger.info(f"Successfully indexed chunk {chunk_id} for document {document_id}")
            return True
            
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
            
            # Configure hybrid search options
            search_options = {
                "search_text": query,
                "vector_queries": [
                    {
                        "kind": "vector",
                        "field": "embedding",
                        "k": top,
                        "vector": query_embedding
                    }
                ],
                "select": ["id", "document_id", "content", "metadata", "chunk_index"],
                "top": top,
                "include_total_count": True
            }
            
            # Execute hybrid search
            results = self.search_client.search(**search_options)
            
            processed_results = []
            for result in results:
                result_data = {
                    "id": result["id"],
                    "document_id": result["document_id"],
                    "content": result["content"],
                    "metadata": json.loads(result["metadata"]),
                    "chunk_index": result["chunk_index"],
                    "score": result["@search.score"],
                    "reranker_score": result.get("@search.reranker_score"),
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

    @azure_retry()
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
                search_text="",  # Empty string for pure vector search
                vector_queries=[
                    {
                        "kind": "vector",
                        "fields": "embedding",  # Field to search in
                        "k": top,  # Number of results to return
                        "vector": query_embedding  # Vector to search for
                    }
                ],
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
            
            self.log_success(f"Vector search found {len(processed_results)} results")
            return processed_results
            
        except Exception as e:
            self.log_error("Vector similarity search failed", e)
            raise

    @azure_retry()
    def hybrid_search(
        self, 
        query: str, 
        top: int = 5, 
        load_full_content: bool = False,
        filter_expr: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search using both vector embeddings and text similarity.
        
        Args:
            query: Search query text
            top: Maximum number of results to return
            load_full_content: Whether to load full content for search results
            filter_expr: Optional OData filter expression
            
        Returns:
            List of search results with hybrid scores
        """
        try:
            # Generate embedding for the query
            query_embedding = self.generate_embedding(query)
            
            # Configure hybrid search options
            search_options = {
                "search_text": query,
                "vector_queries": [
                    {
                        "kind": "vector",
                        "fields": "embedding",  # Field to search in
                        "k": top,  # Number of results to return
                        "vector": query_embedding  # Vector to search for
                    }
                ],
                "filter": filter_expr,  # Apply filter to text portion
                "select": ["id", "document_id", "content", "metadata", "chunk_index"],
                "top": top,
                "include_total_count": True
            }
            
            # Execute hybrid search
            results = self.search_client.search(**search_options)
            
            processed_results = []
            for result in results:
                result_data = {
                    "id": result["id"],
                    "document_id": result["document_id"],
                    "content": result["content"],
                    "metadata": json.loads(result["metadata"]),
                    "chunk_index": result["chunk_index"],
                    "score": result["@search.score"],
                    "reranker_score": result.get("@search.reranker_score"),
                    "vector_score": result.get("@search.vector_score"),
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
            logger.error(f"Hybrid search failed: {str(e)}")
            raise 