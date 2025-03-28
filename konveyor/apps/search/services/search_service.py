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
    VectorSearchAlgorithmMetric,
    VectorSearchAlgorithmConfiguration
)
from openai import AzureOpenAI
from langchain_openai import AzureOpenAIEmbeddings
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from django.conf import settings
from azure.core.exceptions import AzureError
from tenacity import stop_after_attempt, wait_exponential, retry_if_exception_type
from tenacity import stop_after_attempt, wait_exponential, retry_if_exception_type
from azure.storage.blob import BlobServiceClient
from azure.storage.blob import ContentSettings
import uuid
from django.utils import timezone
from konveyor.apps.documents.services.document_service import DocumentService
from konveyor.apps.documents.models import DocumentChunk
from konveyor.utils.azure.openai_client import AzureOpenAIClient

logger = logging.getLogger(__name__)

class SearchService:
    """Service for interacting with Azure Cognitive Search."""
    
    def __init__(self):
        """Initialize search service with detailed logging and validation."""
        logger.info("Initializing SearchService...")
        
        # 1. Validate and log settings
        self.search_endpoint = settings.AZURE_SEARCH_ENDPOINT
        self.search_key = settings.AZURE_SEARCH_API_KEY
        self.index_name = settings.AZURE_SEARCH_INDEX_NAME
        
        if not self.search_endpoint or not self.search_key:
            error_msg = "AZURE_SEARCH_ENDPOINT and AZURE_SEARCH_API_KEY must be configured"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info(f"Search endpoint: {self.search_endpoint}")
        logger.info(f"Search index name: {self.index_name}")
        
        # 2. Initialize and validate OpenAI client and embeddings
        openai_endpoint = settings.AZURE_OPENAI_ENDPOINT
        openai_key = settings.AZURE_OPENAI_API_KEY
        openai_version = settings.AZURE_OPENAI_API_VERSION
        embedding_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-ada-002")
        
        logger.info(f"OpenAI endpoint: {openai_endpoint}")
        logger.info(f"OpenAI API version: {openai_version}")
        logger.info(f"OpenAI embedding deployment: {embedding_deployment}")
        
        if not openai_endpoint or not openai_key:
            logger.warning("Azure OpenAI credentials not configured. Embedding generation will not work.")
            self.openai_client = None
            self.embeddings = None
            self.azure_openai_client = None
        else:
            try:
                # Fix for Azure OpenAI endpoint that may already include a deployment
                base_endpoint = openai_endpoint
                if "/deployments/" in openai_endpoint:
                    # Extract the base endpoint by removing the deployment part
                    base_endpoint = openai_endpoint.split("/deployments/")[0]
                    logger.info(f"Extracted base OpenAI endpoint: {base_endpoint}")
                
                # Initialize our custom Azure OpenAI client
                self.azure_openai_client = AzureOpenAIClient(
                    api_key=openai_key,
                    endpoint=base_endpoint,
                    gpt_deployment=os.getenv("AZURE_OPENAI_GPT_DEPLOYMENT", "gpt-deployment"),
                    embeddings_deployment=embedding_deployment
                )
                logger.info("Successfully initialized AzureOpenAIClient")
                
                # Initialize regular OpenAI client for completions (for backward compatibility)
                # Use API version appropriate for GPT models
                gpt_api_version = openai_version
                self.openai_client = AzureOpenAI(
                    azure_endpoint=base_endpoint,
                    api_key=openai_key,
                    api_version=gpt_api_version
                )
                logger.info(f"Successfully initialized Azure OpenAI client with API version {gpt_api_version}")
                
                # Initialize LangChain embeddings with a version known to work with embeddings
                embeddings_api_version = os.getenv("AZURE_OPENAI_EMBEDDING_API_VERSION", "2023-05-15")
                self.embeddings = AzureOpenAIEmbeddings(
                    azure_deployment=embedding_deployment,
                    openai_api_version=embeddings_api_version,
                    azure_endpoint=base_endpoint,
                    api_key=openai_key
                )
                logger.info(f"Successfully initialized AzureOpenAIEmbeddings with model {embedding_deployment} and API version {embeddings_api_version}")
                
                # Test embedding generation
                try:
                    # Keep test very short to avoid unnecessary token usage
                    test_embedding = self.generate_embedding("test")
                    logger.info(f"Test embedding generation successful: {len(test_embedding)} dimensions")
                except Exception as e:
                    logger.warning(f"Test embedding generation failed: {str(e)}")
                    if "404" in str(e):
                        logger.error(f"Make sure you have deployed the embedding model '{embedding_deployment}' in your Azure OpenAI resource")
                        logger.error(f"Check the deployment name in AZURE_OPENAI_EMBEDDING_DEPLOYMENT environment variable")
            except Exception as e:
                logger.error(f"Failed to initialize Azure OpenAI services: {str(e)}")
                self.openai_client = None
                self.embeddings = None
                self.azure_openai_client = None
        
        # 3. Initialize and validate search clients
        try:
            self.search_credential = AzureKeyCredential(self.search_key)
            self.index_client = SearchIndexClient(
                endpoint=self.search_endpoint,
                credential=self.search_credential
            )
            
            # Test index client
            try:
                # List indexes to validate connectivity
                indexes = list(self.index_client.list_indexes())
                index_names = [index.name for index in indexes]
                logger.info(f"Successfully connected to search service. Found {len(indexes)} indexes: {', '.join(index_names)}")
            except Exception as e:
                logger.warning(f"Test connection to search index client failed: {str(e)}")
            
            # Initialize search client
            self.search_client = SearchClient(
                endpoint=self.search_endpoint,
                index_name=self.index_name,
                credential=self.search_credential
            )
            logger.info(f"Initialized search client for index: {self.index_name}")
            
        except Exception as e:
            error_msg = f"Failed to initialize Azure Search clients: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # 4. Initialize document service
        try:
            self.document_service = DocumentService()
            logger.info("Successfully initialized DocumentService")
        except Exception as e:
            logger.error(f"Failed to initialize DocumentService: {str(e)}")
            raise
        
        logger.info("SearchService initialization completed successfully")
    
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
                        "dimensions": 1536,
                        "vectorSearchProfile": "embedding-profile"
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
            self.search_client = SearchClient(
                endpoint=self.search_endpoint,
                index_name=index_name,
                credential=self.search_credential
            )
            logger.info(f"Updated search client to use index: {index_name}")
            
            return True
        except Exception as e:
            logger.error(f"Failed to create index {index_name}: {e}")
            if "vectorSearch.algorithms[0].kind" in str(e):
                logger.error("The 'kind' field is required but was not properly set. Check your SDK version compatibility.")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
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
        logger.info(f"Generating embedding for text ({len(text)} chars)...")
        
        if self.azure_openai_client:
            # Use our custom client if available
            try:
                return self.azure_openai_client.generate_embedding(text)
            except Exception as e:
                logger.warning(f"Failed to generate embedding with custom client: {str(e)}. Falling back to LangChain.")
        
        if not self.embeddings:
            error_msg = "Azure OpenAI Embeddings not configured correctly"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        try:
            # Truncate text if too long (OpenAI has token limits)
            truncated_text = text[:8000]  # Adjust limit based on your needs
            if len(truncated_text) < len(text):
                logger.info(f"Truncated text from {len(text)} to {len(truncated_text)} chars")
            
            # Get the deployment name from environment variable for logging
            embedding_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-ada-002")
            logger.info(f"Using OpenAI embedding deployment: {embedding_deployment}")
            
            logger.info("Generating embedding with LangChain...")
            # LangChain handles the API call and response parsing
            embedding = self.embeddings.embed_query(truncated_text)
            
            logger.info(f"Successfully generated embedding with {len(embedding)} dimensions")
            return embedding
            
        except Exception as e:
            error_msg = f"Error generating embedding: {str(e)}"
            logger.error(error_msg)
            
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
        embedding: List[float]
    ) -> bool:
        """
        Index a document chunk in Azure Cognitive Search.
        Content should already be stored in blob storage by DocumentService.
        
        Returns:
            bool: True if indexing was successful
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
            
            # Configure hybrid search options with semantic ranking
            search_options = {
                "search_text": query,
                "vector_queries": [
                    {
                        "kind": "vector",
                        "fields": ["embedding"],
                        "k": top,
                        "vector": query_embedding
                    }
                ],
                "select": ["id", "document_id", "content", "metadata", "chunk_index"],
                "query_type": "semantic",
                "query_language": "en-us",
                "semantic_configuration_name": "default",
                "top": top,
                "query_caption": "extractive",  # Get relevant excerpts
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

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(AzureError),
        reraise=True
    )
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
                        "fields": ["embedding"],
                        "k": top,
                        "vector": query_embedding,
                        "filter": filter_expr  # Apply filter to vector portion
                    }
                ],
                "filter": filter_expr,  # Apply filter to text portion
                "select": ["id", "document_id", "content", "metadata", "chunk_index"],
                "query_type": "semantic",
                "query_language": "en-us",
                "semantic_configuration_name": "default",
                "top": top,
                "query_caption": "extractive",
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