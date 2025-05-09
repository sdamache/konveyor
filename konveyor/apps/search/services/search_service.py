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

import json
from typing import Any, Dict, List, Optional, Tuple  # noqa: F401

# Removed django.conf settings
from azure.core.exceptions import (  # Keep for potential specific error handling  # noqa: E501, F401
    AzureError,
)

# Removed tenacity, azure.core.credentials, azure.search.documents.SearchClient
# Keep SearchIndexClient for index management if needed by create_search_index
# Removed: from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (  # noqa: E501, F401
    HnswAlgorithmConfiguration,
    SearchableField,
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    SimpleField,
    VectorSearch,
    VectorSearchAlgorithmConfiguration,
    VectorSearchAlgorithmKind,
    VectorSearchAlgorithmMetric,
    VectorSearchProfile,
)
from openai import (  # Keep for type hinting if needed, though client comes from manager  # noqa: E501, F401
    AzureOpenAI,
)

from konveyor.apps.documents.models import DocumentChunk
from konveyor.core.azure_utils.mixins import (  # noqa: F401, F401, F401
    AzureClientMixin,
    AzureServiceConfig,
    ServiceLoggingMixin,
)
from konveyor.core.azure_utils.retry import azure_retry
from konveyor.core.azure_utils.service import AzureService
from konveyor.core.documents.document_service import DocumentService

# Removed azure.storage.blob.BlobServiceClient
# Removed django.utils.timezone


# Removed module-level logger, rely on self.log_* from AzureService


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
        super().__init__("SEARCH")
        self.log_init("SearchService")

        # Get configuration
        self.index_name = self.config.get_setting(
            "AZURE_SEARCH_INDEX_NAME", default="konveyor-documents"
        )
        self.log_info(
            f"Search index name set to: {self.index_name}"
        )  # Use log_info for config details

        # Get OpenAI configuration
        # Fetch OpenAI config settings using self.config
        openai_version = self.config.get_setting(
            "AZURE_OPENAI_API_VERSION", default="2024-12-01-preview"
        )
        embedding_deployment = self.config.get_setting(
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT", default="embeddings"
        )
        self.log_info(f"Using OpenAI API version: {openai_version}")
        self.log_info(f"Using OpenAI embedding deployment: {embedding_deployment}")

        try:
            # Initialize search clients
            self.index_client, self.search_client = (
                self.client_manager.get_search_clients(self.index_name)
            )

            # Test index client
            indexes = list(self.index_client.list_indexes())
            index_names = [index.name for index in indexes]
            self.log_info(
                f"Found {len(indexes)} existing indexes: {', '.join(index_names)}"
            )

            # Initialize OpenAI client
            self.openai_client = self.client_manager.get_openai_client()

            # Test embedding generation
            test_embedding = self.generate_embedding("test")
            self.log_info(
                f"Test embedding generation successful: {len(test_embedding)} dimensions"  # noqa: E501
            )

            # Initialize document service
            self.document_service = DocumentService()
            self.log_info("Successfully initialized DocumentService")

            self.log_info("SearchService initialization completed successfully")

        except Exception as e:
            self.log_error("Failed to initialize service", e)
            raise

    def create_search_index(self, index_name=None):
        """
        Create the search index if it doesn't exist, with detailed logging.
        """
        self.log_info("Attempting to create search index...")

        # Use provided index_name or fall back to settings
        index_name = index_name or self.index_name
        self.log_info(f"Target index name: {index_name}")

        # Check if index already exists
        try:
            existing_indices = [
                index.name for index in self.index_client.list_indexes()
            ]
            if index_name in existing_indices:
                self.log_info(
                    f"Index '{index_name}' already exists, skipping creation."
                )
                return True
            self.log_info(
                f"Index '{index_name}' does not exist, proceeding with creation."
            )
        except Exception as e:
            self.log_warning(
                f"Could not definitively check if index '{index_name}' exists",
                exc_info=e,
            )

        self.log_info("Defining vector search configuration...")
        try:
            # Define vector search algorithm with explicit parameters to avoid SDK version issues  # noqa: E501
            algorithm_config = {
                "name": "default-algorithm-config",
                "kind": "hnsw",  # Explicitly set kind as a string
                "hnsw_parameters": {
                    "m": 4,
                    "efConstruction": 400,
                    "efSearch": 500,
                    "metric": "cosine",
                },
            }

            self.log_info(
                f"Defined algorithm config: {algorithm_config['name']}, kind: {algorithm_config['kind']}"  # noqa: E501
            )

            # Create vector search configuration with profiles
            vector_search = {
                "algorithms": [algorithm_config],
                "profiles": [
                    {
                        "name": "embedding-profile",
                        "algorithm_configuration_name": "default-algorithm-config",
                        "algorithm": "default-algorithm-config",
                        "vector_fields": ["embedding"],
                    }
                ],
            }

            self.log_info(
                f"Defined vector search profile: 'embedding-profile', algorithm: {vector_search['profiles'][0]['algorithm_configuration_name']}"  # noqa: E501
            )

        except Exception as e:
            self.log_error("Failed to define vector search configuration", exc_info=e)
            raise

        self.log_info("Defining index fields...")
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
                        "sortable": True,
                    },
                    {
                        "name": "chunk_id",
                        "type": "Edm.String",
                        "searchable": False,
                        "filterable": True,
                        "sortable": False,
                    },
                    {
                        "name": "document_id",
                        "type": "Edm.String",
                        "searchable": False,
                        "filterable": True,
                        "sortable": False,
                    },
                    {
                        "name": "chunk_index",
                        "type": "Edm.Int32",
                        "searchable": False,
                        "filterable": True,
                        "sortable": True,
                    },
                    {
                        "name": "content",
                        "type": "Edm.String",
                        "searchable": True,
                        "filterable": False,
                        "sortable": False,
                        "analyzer_name": "standard.lucene",
                    },
                    {
                        "name": "metadata",
                        "type": "Edm.String",
                        "searchable": False,
                        "filterable": False,
                        "sortable": False,
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
                        "nullable": True,  # Allow null values for embedding field
                    },
                ],
                "vectorSearch": vector_search,
            }

            self.log_info(f"Attempting to create index '{index_name}' in Azure...")
            try:
                # Use SearchIndex object directly for creation/update
                from azure.search.documents.indexes.models import SearchIndex

                index = SearchIndex.deserialize(index_definition)
                # Use create_or_update_index for idempotency, but with the SearchIndex object  # noqa: E501
                self.index_client.create_or_update_index(index)
                self.log_success(
                    f"Successfully created/updated index '{index_name}' using SearchIndex object."  # noqa: E501
                )
            except Exception as e:
                self.log_error(
                    f"Index creation/update failed for '{index_name}'.", exc_info=e
                )
                # Re-raise the exception after logging
                raise e

            # Removed manual update of self.search_client.
            # The client obtained in __init__ via AzureClientManager should be used.
            # If an index with a *different* name was created, the service instance
            # might not be correctly configured for it without re-initialization
            # or fetching a new client specifically for that index via client_manager.
            # Assuming for now the service operates on the index set during init.
            self.log_info(f"Index creation process completed for '{index_name}'.")

            return True
        except Exception as e:
            self.log_error(f"Failed to create index '{index_name}'", exc_info=e)
            if "vectorSearch.algorithms[0].kind" in str(e):
                self.log_error(
                    "Potential SDK version issue: 'kind' field might be missing or invalid in vectorSearch config."  # noqa: E501
                )
            raise

    @azure_retry()
    def generate_embedding(self, text: str) -> list[float]:
        """
        Generate an embedding for the given text using LangChain's AzureOpenAIEmbeddings.  # noqa: E501
        Includes retry logic for resilience and detailed logging.

        Args:
            text: The text to generate an embedding for

        Returns:
            The embedding as a list of floats

        Raises:
            Exception: If embedding generation fails after retries
        """
        self.log_info(
            f"Generating embedding for text ({len(text)} chars)..."
        )  # Use log_info

        if not self.openai_client:
            error_msg = "Azure OpenAI client not configured or initialization failed."
            self.log_error(error_msg)
            raise ValueError(error_msg)

        # Use Azure OpenAI client
        try:
            # Get deployment name from environment variable
            embedding_deployment = self.config.get_setting(
                "AZURE_OPENAI_EMBEDDING_DEPLOYMENT", default="embeddings"
            )
            self.log_info(
                f"Using embedding deployment: {embedding_deployment}"
            )  # Use log_info

            # Truncate text if too long (OpenAI has token limits)
            # Simple truncation, consider more sophisticated chunking for production
            truncated_text = text[:8191]  # Max tokens for ada-002 is 8191
            if len(truncated_text) < len(text):
                self.log_info(
                    f"Truncated text from {len(text)} to {len(truncated_text)} chars for embedding"  # noqa: E501
                )

            self.log_info(
                f"Calling OpenAI Embeddings API: Endpoint='{self.openai_client.base_url}', "  # noqa: E501
                f"API Version='{self.openai_client._api_version}', Deployment='{embedding_deployment}'"  # Use private _api_version  # noqa: E501
            )

            response = self.openai_client.embeddings.create(
                model=embedding_deployment, input=truncated_text
            )
            embedding = response.data[0].embedding
            self.log_info(
                f"Generated embedding with {len(embedding)} dimensions"
            )  # Use log_info
            return embedding
        except Exception as e:
            # Log specific details for 404 errors
            if hasattr(e, "status_code") and e.status_code == 404:
                self.log_error(
                    f"404 error generating embedding. Check Azure OpenAI deployment '{embedding_deployment}'. "  # noqa: E501
                    f"Verify endpoint, key, and deployment name/status in Azure portal.",  # noqa: E501
                    exc_info=False,  # Don't need full stack trace for this specific message  # noqa: E501
                )
            # Removed redundant logger.error call, self.log_error below captures the full exception  # noqa: E501
            self.log_error(
                "Failed to generate embedding with Azure OpenAI client", exc_info=e
            )  # Add exc_info=e
            raise

    def delete_index(self) -> None:
        """Delete the search index if it exists."""
        try:
            self.index_client.delete_index(self.index_name)
            self.log_info(
                f"Search index '{self.index_name}' deleted successfully."
            )  # Use log_info for successful operations
        except Exception as e:
            self.log_error(
                f"Failed to delete search index '{self.index_name}'", exc_info=e
            )  # Keep as error
            raise

    def get_index(self) -> SearchIndex:
        """Get the current search index configuration."""
        try:
            return self.index_client.get_index(self.index_name)
        except Exception as e:
            self.log_error(
                f"Failed to get search index '{self.index_name}'", exc_info=e
            )  # Keep as error
            raise

    # Removed tenacity @retry decorator. Rely on core retry mechanisms or add @azure_retry if needed.  # noqa: E501
    # Consider adding @azure_retry() here if the upload_documents call itself doesn't handle retries sufficiently.  # noqa: E501
    # For now, assuming the underlying SDK call or core client handles retries.
    def index_document_chunk(
        self,
        chunk_id: str,
        document_id: str,
        content: str,
        chunk_index: int,
        metadata: dict[str, Any],
        embedding: list[float] | None = None,
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
            embedding: Optional pre-computed embedding. If None, will be generated from content.  # noqa: E501

        Returns:
            bool: True if indexing was successful
        """
        try:
            # Generate embedding if not provided
            if embedding is None and content:
                try:
                    embedding = self.generate_embedding(content)
                except Exception as e:
                    self.log_warning(
                        f"Failed to generate embedding for chunk {chunk_id}, proceeding without embedding.",  # noqa: E501
                        exc_info=e,
                    )  # Keep as warning
                    embedding = None

            # Prepare document for indexing
            search_document = {
                "id": chunk_id,
                "document_id": document_id,
                "chunk_index": chunk_index,
                "content": content[:8000],  # Store a preview in search index
                "metadata": json.dumps(metadata),
            }

            # Only include embedding if we have one
            if embedding is not None:
                search_document["embedding"] = embedding

            result = self.search_client.upload_documents(documents=[search_document])

            if not result[0].succeeded:
                error_msg = (
                    f"Indexing failed for chunk {chunk_id}: {result[0].error_message}"
                )
                self.log_error(error_msg)  # Keep as error
                raise Exception(error_msg)

            self.log_info(
                f"Successfully indexed chunk {chunk_id} for document {document_id}"
            )  # Keep as info
            return True

        except Exception as e:
            self.log_error(
                f"Error indexing document chunk {chunk_id}", exc_info=e
            )  # Keep as error
            raise

    def get_chunk_content(self, chunk_id: str, document_id: str) -> str:
        """
        Retrieve chunk content using DocumentService.
        """
        return self.document_service.get_chunk_content(
            DocumentChunk.objects.get(id=chunk_id, document_id=document_id)
        )

    # Removed semantic_search method as it's considered redundant with hybrid_search
    # and was marked for removal in the modernization plan.
    @azure_retry()
    def vector_similarity_search(
        self, query: str, top: int = 5, filter_expr: str | None = None
    ) -> list[dict[str, Any]]:
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
                        "vector": query_embedding,  # Vector to search for
                    }
                ],
                select=["id", "document_id", "content", "metadata", "chunk_index"],
                filter=filter_expr,
                top=top,
            )

            processed_results = []
            for result in results:
                processed_results.append(
                    {
                        "id": result["id"],
                        "document_id": result["document_id"],
                        "content": result["content"],
                        "metadata": json.loads(result["metadata"]),
                        "chunk_index": result["chunk_index"],
                        "similarity_score": result["@search.score"],
                    }
                )

            self.log_info(
                f"Vector search found {len(processed_results)} results"
            )  # Use log_info
            return processed_results

        except Exception as e:
            self.log_error(
                "Vector similarity search failed", exc_info=e
            )  # Add exc_info=e
            raise

    @azure_retry()
    def hybrid_search(
        self,
        query: str,
        top: int = 5,
        load_full_content: bool = False,
        filter_expr: str | None = None,
    ) -> list[dict[str, Any]]:
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
                        "vector": query_embedding,  # Vector to search for
                    }
                ],
                "filter": filter_expr,  # Apply filter to text portion
                "select": ["id", "document_id", "content", "metadata", "chunk_index"],
                "top": top,
                "include_total_count": True,
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
                    "highlights": result.get("@search.highlights", {}).get(
                        "content", []
                    ),
                    "captions": [c.text for c in result.get("@search.captions", [])],
                }

                if load_full_content:
                    try:
                        result_data["full_content"] = self.get_chunk_content(
                            result["id"], result["document_id"]
                        )
                    except Exception as e:
                        self.log_warning(
                            f"Could not load full content for chunk {result['id']}",
                            exc_info=e,
                        )
                        result_data["full_content_error"] = str(e)

                processed_results.append(result_data)

            return processed_results

        except Exception as e:
            self.log_error(f"Hybrid search failed for query: '{query}'", exc_info=e)
            raise
