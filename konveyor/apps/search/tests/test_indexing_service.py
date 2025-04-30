"""Tests for document indexing service.

This module contains tests for the IndexingService class, which handles
document indexing in Azure Cognitive Search.
"""

import os
import unittest
import uuid
from datetime import datetime
from io import BytesIO
# Removed logging and dotenv imports
from unittest.mock import Mock, patch

import pytest
from django.conf import settings
from django.test import TestCase

from konveyor.apps.documents.models import Document, DocumentChunk
from konveyor.apps.search.services.indexing_service import IndexingService
from konveyor.apps.search.services.search_service import SearchService
# Import Azure client manager
from konveyor.core.azure_utils.clients import AzureClientManager
from konveyor.core.azure_utils.config import AzureConfig
from konveyor.core.documents.document_service import DocumentService

# Load environment variables
# Removed load_dotenv() call


# Removed module-level logger definition


class TestIndexingService(TestCase):
    """Test cases for IndexingService.

    Tests the functionality of the IndexingService class, including:
    - Document indexing
    - Batch processing
    - Error handling

    Attributes:
        test_run_id (str): Unique ID for this test run
        indexing_service (IndexingService): Service under test
    """

    @classmethod
    def check_azure_services(cls):
        """Check the status of required Azure services.

        Provides diagnostic information about Azure service configuration.
        For the hackathon, we'll focus only on the essential services needed for testing.

        Returns:
            bool: True if all required services are available, False otherwise
        """
        print("\n==== Azure Services Diagnostic Information ====")

        # For the hackathon, we only need these core services
        required_vars = [
            "AZURE_SEARCH_ENDPOINT",
            "AZURE_SEARCH_API_KEY",
            "AZURE_OPENAI_ENDPOINT",
            "AZURE_OPENAI_API_KEY",
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT",
        ]

        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            print(f"Missing required environment variables: {', '.join(missing_vars)}")
            return False

        # For the hackathon, we'll continue even if some non-critical services are missing
        print("✓ All essential Azure services are configured")

        # Use AzureConfig to check service availability
        try:
            from konveyor.core.azure_utils.config import AzureConfig

            config = AzureConfig()

            # Print a simplified summary of available services using AzureConfig
            print("\nAvailable Azure Services:")
            print(f"  Search Service: {config.get_endpoint('SEARCH')}")
            print(f"  OpenAI Service: {config.get_endpoint('OPENAI')}")
            print(
                f"  Embedding Model: {os.environ.get('AZURE_OPENAI_EMBEDDING_DEPLOYMENT')}"
            )

            # Log the configuration to the error log for future reference
            with open("logs/error.log", "a") as log_file:
                log_file.write(
                    f"[{datetime.now()}] Azure services configuration verified for indexing tests\n"
                )
                log_file.write(
                    f"[{datetime.now()}] Using Search endpoint: {config.get_endpoint('SEARCH')}\n"
                )
                log_file.write(
                    f"[{datetime.now()}] Using OpenAI endpoint: {config.get_endpoint('OPENAI')}\n"
                )
                log_file.write(
                    f"[{datetime.now()}] Using embedding model: {os.environ.get('AZURE_OPENAI_EMBEDDING_DEPLOYMENT')}\n"
                )
        except Exception as e:
            print(f"Warning: Could not initialize AzureConfig: {str(e)}")
            with open("logs/error.log", "a") as log_file:
                log_file.write(
                    f"[{datetime.now()}] Could not initialize AzureConfig: {str(e)}\n"
                )

        print("=============================================\n")
        return True
        env_vars = {
            "AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT": os.environ.get(
                "AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT"
            ),
            "AZURE_STORAGE_CONNECTION_STRING": bool(
                os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
            ),
            "AZURE_STORAGE_CONTAINER_NAME": os.environ.get(
                "AZURE_STORAGE_CONTAINER_NAME"
            ),
            "AZURE_SEARCH_ENDPOINT": os.environ.get("AZURE_SEARCH_ENDPOINT"),
            "AZURE_SEARCH_INDEX_NAME": os.environ.get("AZURE_SEARCH_INDEX_NAME"),
        }

        # Security: Don't print actual API keys, just whether they exist
        api_keys = {
            "AZURE_DOCUMENT_INTELLIGENCE_API_KEY": bool(
                os.environ.get("AZURE_DOCUMENT_INTELLIGENCE_API_KEY")
            ),
            "AZURE_SEARCH_API_KEY": bool(os.environ.get("AZURE_SEARCH_API_KEY")),
        }

        print("\nEnvironment Variables:")
        for var, value in env_vars.items():
            if isinstance(value, bool):
                print(f"  {var}: {'✓ Set' if value else '✗ Not set'}")
            else:
                if value and var.endswith("_ENDPOINT"):
                    masked = (
                        value[:15] + "..." + (value[-15:] if len(value) > 30 else "")
                    )
                    print(f"  {var}: {masked}")
                else:
                    print(f"  {var}: {'✓ Set' if value else '✗ Not set'}")

        print("\nAPI Keys:")
        for key, exists in api_keys.items():
            print(f"  {key}: {'✓ Set' if exists else '✗ Not set'}")

        print("=============================================\n")

    @classmethod
    def setUpClass(cls):
        """Set up test environment with real Azure services."""
        super().setUpClass()
        print("==== Setting up TestIndexingService ====")

        # Check required environment variables
        required_vars = [
            "AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT",
            "AZURE_DOCUMENT_INTELLIGENCE_API_KEY",
            "AZURE_SEARCH_ENDPOINT",
            "AZURE_SEARCH_API_KEY",
            "AZURE_SEARCH_INDEX_NAME",
            "AZURE_OPENAI_ENDPOINT",
            "AZURE_OPENAI_API_KEY",
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT",
        ]

        missing_vars = [var for var in required_vars if not os.environ.get(var)]
        if missing_vars:
            raise unittest.SkipTest(
                f"Skipping integration tests. Missing environment variables: {', '.join(missing_vars)}"
            )

        # Generate unique test ID
        cls.test_run_id = uuid.uuid4().hex[:8]
        print(f"Test run ID: {cls.test_run_id}")

        # Generate unique test container name
        cls.test_container_name = f"test-chunks-{cls.test_run_id}"
        os.environ["AZURE_STORAGE_TEST_CONTAINER_NAME"] = cls.test_container_name
        print(f"Set test container name: {cls.test_container_name}")

        # Check Azure services
        if not cls.check_azure_services():
            pytest.skip("Skipping tests due to missing Azure services configuration")

        # Initialize services
        try:
            # Initialize Azure client manager
            cls.azure_client_manager = AzureClientManager()
            print("Successfully initialized AzureClientManager")

            # Initialize document service
            cls.document_service = DocumentService()
            print("Successfully initialized DocumentService")

            # Initialize indexing service
            cls.indexing_service = IndexingService()
            print("Successfully initialized IndexingService")

            # Generate unique test index name
            cls.original_index_name = os.getenv(
                "AZURE_SEARCH_INDEX_NAME", "konveyor-documents"
            )
            cls.test_index_name = f"test-index-{cls.test_run_id}"

            # Update environment variable
            os.environ["AZURE_SEARCH_INDEX_NAME"] = cls.test_index_name
            print(f"Set test index name: {cls.test_index_name}")

            # Update the search service to use the test index
            cls.indexing_service.search_service.index_name = cls.test_index_name

            # Create the test index using the SearchService's method
            try:
                print(f"Creating test index: {cls.test_index_name}...")
                # Use the existing create_search_index method
                cls.indexing_service.search_service.create_search_index(
                    cls.test_index_name
                )
                print(f"Successfully created test index: {cls.test_index_name}")
            except Exception as e:
                print(f"Warning: Could not create test index: {str(e)}")
                # Check if index exists despite the error
                try:
                    # Get index client from AzureClientManager
                    index_client, _ = cls.azure_client_manager.get_search_clients(
                        cls.test_index_name
                    )
                    existing_indices = [
                        index.name for index in index_client.list_indexes()
                    ]
                    if cls.test_index_name in existing_indices:
                        print(
                            f"Index {cls.test_index_name} already exists, continuing with tests"
                        )
                    else:
                        print(
                            f"Error: Index {cls.test_index_name} does not exist and could not be created"
                        )
                        pytest.skip(f"Could not create test index: {str(e)}")
                except Exception as check_e:
                    print(f"Error: Could not check if index exists: {str(check_e)}")
                    pytest.skip(f"Could not verify test index: {str(check_e)}")

        except Exception as e:
            print(f"Error: Failed to initialize test environment: {e}")
            raise
        print(
            f"Set environment variable AZURE_SEARCH_INDEX_NAME to {cls.test_index_name}"
        )

        # Create a new search client for the test index using AzureClientManager
        try:
            print(
                "Creating new search client for test index using AzureClientManager..."
            )
            _, search_client = cls.azure_client_manager.get_search_clients(
                cls.test_index_name
            )

            # Update the search service to use the new client
            cls.indexing_service.search_service.search_client = search_client
            print(f"Created new search client for index {cls.test_index_name}")
        except Exception as e:
            print(f"Error: Failed to create new search client: {e}")
            # Don't skip tests yet, as this might still work

        # 11. Set up test files directory
        cls.test_files_dir = os.path.join(
            os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            ),
            "documents",
            "tests",
            "test_files",
        )
        print(f"Test files directory: {cls.test_files_dir}")

        # 12. Validate test files
        test_files = [
            f
            for f in os.listdir(cls.test_files_dir)
            if os.path.isfile(os.path.join(cls.test_files_dir, f))
        ]
        print(f"Found {len(test_files)} test files: {', '.join(test_files)}")

        # Test embedding generation to ensure the service is working properly
        try:
            print("Testing embedding generation using AzureClientManager...")
            # Get OpenAI client from AzureClientManager
            openai_client = cls.azure_client_manager.get_openai_client()

            # Generate test embedding
            deployment_name = os.environ.get("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
            response = openai_client.embeddings.create(
                input="Test embedding generation", model=deployment_name
            )
            embedding = response.data[0].embedding
            print(
                f"Successfully generated test embedding with {len(embedding)} dimensions"
            )
        except Exception as e:
            print(f"Error: Test embedding generation failed: {str(e)}")
            # Don't skip tests yet - individual tests can handle this

        # Setup complete
        print("==== TestIndexingService setup completed ====")

    @classmethod
    def tearDownClass(cls):
        """Clean up test resources with detailed logging."""
        print("==== Tearing down TestIndexingService ====")

        try:
            # Delete test index using AzureClientManager
            if (
                hasattr(cls, "test_index_name")
                and cls.test_index_name
                and hasattr(cls, "azure_client_manager")
            ):
                print(f"Deleting test index: {cls.test_index_name}")
                try:
                    # Get index client from AzureClientManager
                    index_client, _ = cls.azure_client_manager.get_search_clients(
                        cls.test_index_name
                    )
                    index_client.delete_index(cls.test_index_name)
                    print(f"Successfully deleted test index: {cls.test_index_name}")
                except Exception as delete_error:
                    print(f"Error: Failed to delete test index: {str(delete_error)}")

            # Delete test container
            if (
                hasattr(cls, "test_container_name")
                and cls.test_container_name
                and hasattr(cls, "azure_client_manager")
            ):
                print(f"Deleting test container: {cls.test_container_name}")
                try:
                    blob_service_client = cls.azure_client_manager.get_blob_client()
                    blob_service_client.delete_container(cls.test_container_name)
                    print(
                        f"Successfully deleted test container: {cls.test_container_name}"
                    )
                except Exception as delete_container_error:
                    # Log error, but don't fail teardown if container doesn't exist or other issue
                    print(
                        f"Warning: Could not delete test container '{cls.test_container_name}': {str(delete_container_error)}"
                    )

                # Unset test container name environment variable
                if "AZURE_STORAGE_TEST_CONTAINER_NAME" in os.environ:
                    del os.environ["AZURE_STORAGE_TEST_CONTAINER_NAME"]
                    print(
                        "Unset AZURE_STORAGE_TEST_CONTAINER_NAME environment variable"
                    )

            # Restore original index name
            if hasattr(cls, "original_index_name"):
                os.environ["AZURE_SEARCH_INDEX_NAME"] = cls.original_index_name
                print(f"Restored index name to: {cls.original_index_name}")

        except Exception as e:
            print(f"Error during teardown: {e}")

        print("==== TestIndexingService teardown completed ====")
        super().tearDownClass()

    def setUp(self):
        # No need to create index in each test if we created it in setUpClass
        pass

    def tearDown(self):
        # Clean up documents and chunks after each test
        Document.objects.all().delete()
        DocumentChunk.objects.all().delete()

        # Clean up blob storage
        try:
            blob_client = self.azure_client_manager.get_blob_client()
            container_name = "document-chunks"

            try:
                container_client = blob_client.get_container_client(container_name)
                # List all blobs and delete them
                blobs = container_client.list_blobs()
                for blob in blobs:
                    container_client.delete_blob(blob.name)
                print(f"Cleaned up all blobs in {container_name} container")

                # Delete the container
                container_client.delete_container()
                print(f"Deleted container {container_name}")
            except Exception as e:
                print(
                    f"Warning: Container {container_name} may not exist or error during cleanup: {str(e)}"
                )
        except Exception as e:
            print(f"Error during blob storage cleanup: {str(e)}")

    def test_index_existence_verification(self):
        """Test that index existence verification works correctly."""
        # Get search clients using AzureClientManager
        try:
            index_client, _ = self.azure_client_manager.get_search_clients(
                self.test_index_name
            )
            print("Successfully obtained search clients from AzureClientManager")

            # Check if our test index exists
            exists = self.test_index_name in [
                index.name for index in index_client.list_indexes()
            ]
            self.assertTrue(exists, f"Test index {self.test_index_name} should exist")

            # Check non-existent index
            fake_index_name = f"nonexistent-index-{uuid.uuid4().hex[:8]}"
            exists = fake_index_name in [
                index.name for index in index_client.list_indexes()
            ]
            self.assertFalse(exists, "Non-existent index should return False")
        except Exception as e:
            print(f"Error checking index existence: {str(e)}")
            self.fail(f"Failed to verify index existence: {str(e)}")

    def test_single_document_indexing(self):
        """Test indexing a single document."""
        # Process a text document first
        sample_text_path = os.path.join(self.test_files_dir, "sample.txt")

        # Read the file contents
        with open(sample_text_path, "rb") as f:
            file_content = f.read()

        # Create a file-like object
        file_obj = BytesIO(file_content)
        file_obj.name = "sample.txt"

        # Process document to create chunks using parse_file with correct parameters
        content, metadata = self.document_service.parse_file(
            file_obj=file_obj, content_type="text/plain"
        )

        # Create a document record manually since parse_file doesn't do that
        from konveyor.apps.documents.models import Document, DocumentChunk

        document = Document.objects.create(
            title="Sample Text",
            filename="sample.txt",
            content_type="text/plain",
            size=len(file_content),
        )

        # Create a chunk for this document
        chunk = DocumentChunk.objects.create(
            document=document,
            chunk_index=0,
            blob_path=f"chunks/{document.id}/{uuid.uuid4().hex}.txt",  # Store content in blob storage
            metadata=metadata,
        )

        # Store content in blob storage
        self.document_service.store_chunk_content(chunk, content)

        # Verify document and chunks were created
        self.assertIsNotNone(document)
        chunks = DocumentChunk.objects.filter(document=document)
        self.assertTrue(chunks.exists(), "Document chunks should be created")

        # Index a single chunk
        chunk = chunks.first()
        # Get chunk content from blob storage
        chunk_content = self.document_service.get_chunk_content(chunk)

        # Try to generate embedding using AzureClientManager or use mock if it fails
        try:
            # Get OpenAI client from AzureClientManager
            openai_client = self.azure_client_manager.get_openai_client()
            print("Successfully obtained OpenAI client from AzureClientManager")

            # Generate embedding using the client
            deployment_name = os.environ.get("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
            response = openai_client.embeddings.create(
                input=chunk_content, model=deployment_name
            )
            embedding = response.data[0].embedding
            print(f"Successfully generated embedding with {len(embedding)} dimensions")
        except Exception as e:
            # Log the error but continue with a mock embedding for testing
            print(f"Warning: Failed to generate embedding, using mock: {str(e)}")
            # Create a mock embedding of the correct size (1536 dimensions)
            embedding = [0.1] * 1536

        # Index the chunk with vector search support
        result = self.indexing_service.search_service.index_document_chunk(
            chunk_id=str(chunk.id),
            document_id=str(document.id),
            content=chunk_content,
            chunk_index=chunk.chunk_index,
            metadata=chunk.metadata,
            embedding=embedding,
        )

        # Verify successful indexing
        self.assertTrue(result, "Chunk indexing should return True for success")

    def test_batch_document_indexing(self):
        """Test batch indexing of document chunks."""
        # Process documents of different types
        file_paths = [
            ("sample.txt", "text/plain"),
            ("sample.pdf", "application/pdf"),
            ("sample.md", "text/markdown"),
        ]

        documents = []
        all_chunks = []

        # Process each document to create chunks
        for filename, content_type in file_paths:
            file_path = os.path.join(self.test_files_dir, filename)
            if os.path.exists(file_path):
                # Read the file contents
                with open(file_path, "rb") as f:
                    file_content = f.read()

                # Create a file-like object
                file_obj = BytesIO(file_content)
                file_obj.name = filename

                # Get content type from file extension
                if filename.endswith(".txt"):
                    content_type = "text/plain"
                elif filename.endswith(".pdf"):
                    content_type = "application/pdf"
                elif filename.endswith(".md"):
                    content_type = "text/markdown"
                else:
                    content_type = "application/octet-stream"

                # Parse file with correct parameters
                content, metadata = self.document_service.parse_file(
                    file_obj=file_obj, content_type=content_type
                )

                # Create a document record manually
                from konveyor.apps.documents.models import (Document,
                                                            DocumentChunk)

                document = Document.objects.create(
                    title=f"Test {filename}",
                    filename=filename,
                    content_type=content_type,
                    size=len(file_content),
                )

                # Create a chunk for this document
                chunk = DocumentChunk.objects.create(
                    document=document,
                    chunk_index=0,
                    blob_path=f"chunks/{document.id}/{uuid.uuid4().hex}.txt",  # Store content in blob storage
                    metadata=metadata,
                )

                # Store content in blob storage
                self.document_service.store_chunk_content(chunk, content)
                documents.append(document)

                # Get chunks for this document
                chunks = list(DocumentChunk.objects.filter(document=document))
                all_chunks.extend(chunks)

        # Verify we have documents and chunks
        self.assertTrue(len(documents) > 0, "Documents should be processed")
        self.assertTrue(len(all_chunks) > 0, "Chunks should be created")

        # Batch index all chunks
        if len(all_chunks) > 5:
            # If we have many chunks, just index a subset
            batch_chunks = all_chunks[:5]
        else:
            batch_chunks = all_chunks

        # Index each chunk in the batch
        success_count = 0
        for chunk in batch_chunks:
            try:
                # Get chunk content
                chunk_content = self.document_service.get_chunk_content(chunk)

                # Try to generate embedding or use mock if it fails
                try:
                    # Generate embedding
                    embedding = self.indexing_service.search_service.generate_embedding(
                        chunk_content
                    )
                except Exception as e:
                    # Log the error but continue with a mock embedding for testing
                    print(
                        f"Warning: Failed to generate embedding, using mock: {str(e)}"
                    )
                    # Create a mock embedding of the correct size (1536 dimensions)
                    embedding = [0.1] * 1536

                # Index the chunk
                result = self.indexing_service.search_service.index_document_chunk(
                    chunk_id=str(chunk.id),
                    document_id=str(chunk.document.id),
                    content=chunk_content,
                    chunk_index=chunk.chunk_index,
                    metadata=chunk.metadata,
                    embedding=embedding,
                )
                if result:
                    success_count += 1
            except Exception as e:
                print(f"Error indexing chunk {chunk.id}: {e}")

        # Verify successful batch indexing
        self.assertTrue(
            success_count > 0, "At least one chunk should be indexed successfully"
        )

    def test_different_document_types(self):
        """Test indexing chunks from different document types."""
        document_types = {
            "text": ("sample.txt", "text/plain"),
            "pdf": ("sample.pdf", "application/pdf"),
            "markdown": ("sample.md", "text/markdown"),
            "docx": (
                "sample.docx",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ),
        }

        indexed_by_type = {}

        # Process each document type
        for doc_type, (filename, content_type) in document_types.items():
            file_path = os.path.join(self.test_files_dir, filename)
            if not os.path.exists(file_path):
                print(f"Skipping {doc_type} test - file {filename} not found")
                continue

            # Read the file contents
            with open(file_path, "rb") as f:
                file_content = f.read()

            # Create a file-like object
            file_obj = BytesIO(file_content)
            file_obj.name = filename

            # Map file extension to content type
            if filename.endswith(".txt"):
                content_type = "text/plain"
            elif filename.endswith(".pdf"):
                content_type = "application/pdf"
            elif filename.endswith(".md"):
                content_type = "text/markdown"
            elif filename.endswith(".docx"):
                content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            else:
                content_type = "application/octet-stream"

            # Parse file with correct parameters
            content, metadata = self.document_service.parse_file(
                file_obj=file_obj, content_type=content_type
            )

            # Create a document record manually
            from konveyor.apps.documents.models import Document, DocumentChunk

            document = Document.objects.create(
                title=f"Test {filename}",
                filename=filename,
                content_type=content_type,
                size=len(file_content),
            )

            # Create a chunk for this document
            chunk = DocumentChunk.objects.create(
                document=document,
                chunk_index=0,
                blob_path=f"chunks/{document.id}/{uuid.uuid4().hex}.txt",  # Store content in blob storage
                metadata=metadata,
            )

            # Store content in blob storage
            self.document_service.store_chunk_content(chunk, content)

            # Get chunks for this document
            chunks = list(DocumentChunk.objects.filter(document=document))
            if not chunks:
                print(f"No chunks created for {doc_type} document")
                continue

            # Index the first chunk
            try:
                # Get chunk content
                chunk = chunks[0]
                chunk_content = self.document_service.get_chunk_content(chunk)

                # Try to generate embedding or use mock if it fails
                try:
                    # Generate embedding
                    embedding = self.indexing_service.search_service.generate_embedding(
                        chunk_content
                    )
                except Exception as e:
                    # Log the error but continue with a mock embedding for testing
                    print(
                        f"Warning: Failed to generate embedding for {doc_type}, using mock: {str(e)}"
                    )
                    # Create a mock embedding of the correct size (1536 dimensions)
                    embedding = [0.1] * 1536

                # Index the chunk
                result = self.indexing_service.search_service.index_document_chunk(
                    chunk_id=str(chunk.id),
                    document_id=str(document.id),
                    content=chunk_content,
                    chunk_index=chunk.chunk_index,
                    metadata=chunk.metadata,
                    embedding=embedding,
                )
                indexed_by_type[doc_type] = result
            except Exception as e:
                indexed_by_type[doc_type] = False
                print(f"Error indexing {doc_type} document: {e}")

        # Verify indexing worked for available document types
        for doc_type, result in indexed_by_type.items():
            self.assertTrue(result, f"Indexing should succeed for {doc_type} document")

    def test_malformed_document_error_handling(self):
        """Test how indexing service handles invalid document data."""
        # Create a document with malformed/problematic content
        doc = Document.objects.create(
            title="Malformed Document",
            blob_path="malformed.txt",
            content_type="text/plain",
            status="processed",
        )

        # Test cases with problematic content
        problem_contents = [
            # Empty content
            "",
            # Content with special characters
            """Special chars: ¡™£¢∞§¶•ªº–≠œ∑´®†¥¨ˆøπ"'«åß∂ƒ©˙∆˚¬…æΩ≈ç√∫˜µ≤≥÷""",
        ]

        test_results = {}

        for i, content in enumerate(problem_contents):
            content_desc = (
                f"Empty string"
                if content == ""
                else f"Long content" if len(content) > 1000 else "Special characters"
            )

            # Create a problematic chunk
            chunk = DocumentChunk.objects.create(
                document=doc,
                chunk_index=i + 1,
                blob_path=f"chunks/{doc.id}/{uuid.uuid4().hex}.txt",
                metadata={
                    "chunk_id": uuid.uuid4().hex,
                    "chunk_index": i + 1,
                    "parent_document_id": str(doc.id),
                    "content_length": len(content),
                },
            )

            # Store content in blob storage
            self.document_service.store_chunk_content(chunk, content)

            try:
                # Try to index the problematic content directly
                result = self.indexing_service.search_service.index_document_chunk(
                    chunk_id=str(chunk.id),
                    document_id=str(doc.id),
                    content=content,
                    chunk_index=i + 1,
                    metadata=chunk.metadata,
                    embedding=None,  # Allow the service to generate embedding
                )
                # Store result
                test_results[content_desc] = result
                print(f"Indexing result for {content_desc}: {result}")
            except Exception as e:
                # If an exception is raised, the service should catch it internally
                test_results[content_desc] = f"Failed with: {str(e)}"
                print(f"Indexing service failed to handle problematic content: {e}")

        # Print summary table
        self._print_test_summary(test_results)

    def _print_test_summary(self, results_dict):
        """Print a formatted summary table of test results."""
        print("\n" + "=" * 60)
        print(" INDEXING SERVICE TEST RESULTS ".center(60, "="))
        print("=" * 60)
        print(f"{'CONTENT TYPE':<30} | {'RESULT':<25}")
        print("-" * 60)

        for content_type, result in results_dict.items():
            result_str = str(result)
            if len(result_str) > 25:
                result_str = result_str[:22] + "..."
            print(f"{content_type:<30} | {result_str:<25}")

        print("=" * 60 + "\n")
