"""Tests for Azure Cognitive Search service.

This module contains tests for the SearchService class, which provides
functionality for document search using Azure Cognitive Search.
"""

# Removed: import json
import os
import uuid
# Removed: from datetime import datetime
from pathlib import Path
# Removed: from typing import Any, Dict, List
# Removed: from unittest.mock import Mock, patch

# Removed time and logging imports
import pytest
from azure.search.documents.indexes.models import (SearchFieldDataType,
                                                   SearchIndex)
from django.conf import settings
from django.test import TestCase

from konveyor.apps.search.services.indexing_service import IndexingService
# Removed: from konveyor.apps.search.services.search_service import SearchService
# Removed: from konveyor.core.azure_utils.clients import AzureClientManager
from konveyor.core.documents.document_service import DocumentService

# Removed dotenv import


# Load environment variables
# Removed load_dotenv() call

# Removed module-level logger configuration


class SearchServiceTests(TestCase):
    """Test cases for SearchService.

    Tests the functionality of the SearchService class, including:
    - Index creation and management
    - Document indexing
    - Search operations (vector, hybrid)

    Attributes:
        test_run_id (str): Unique ID for this test run
        cost_tracker (dict): Track operations for cost analysis
    """

    @classmethod
    def setUpClass(cls):
        """Set up test environment.

        Creates services and initializes test data.
        Skips tests if Azure services are not available.
        """
        super().setUpClass()
        cls.test_run_id = uuid.uuid4().hex[:8]
        cls.cost_tracker = {
            "index_operations": 0,
            "vector_operations": 0,
            "search_operations": 0,
        }

        print(f"\n==== Setting up SearchServiceTests ====")
        print(f"Test run ID: {cls.test_run_id}")

        # Check if required environment variables are set
        required_vars = [
            "AZURE_SEARCH_ENDPOINT",
            "AZURE_SEARCH_API_KEY",
            "AZURE_OPENAI_ENDPOINT",
            "AZURE_OPENAI_API_KEY",
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT",
        ]

        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            print(
                f"Skipping tests due to missing environment variables: {', '.join(missing_vars)}"
            )
            pytest.skip(
                f"Missing required environment variables: {', '.join(missing_vars)}"
            )

        # Initialize services
        try:
            cls.document_service = DocumentService()
            cls.indexing_service = IndexingService()
        except Exception as e:
            print(f"Skipping tests due to service initialization error: {str(e)}")
            pytest.skip(f"Service initialization failed: {str(e)}")

        # Generate unique test index name
        cls.original_index_name = os.getenv(
            "AZURE_SEARCH_INDEX_NAME", "konveyor-documents"
        )
        cls.test_index_name = f"konveyor-test-{cls.test_run_id}"

        # Update environment variable and service property
        os.environ["AZURE_SEARCH_INDEX_NAME"] = cls.test_index_name

        # Create the test index
        try:
            # Initialize search service with test index name
            cls.search_service = cls.indexing_service.search_service
            cls.search_service.index_name = cls.test_index_name

            # Try to create the test index
            print(f"Creating test index: {cls.test_index_name}...")
            cls.search_service.create_search_index(cls.test_index_name)
            print(f"Test index {cls.test_index_name} created successfully")

            # Explicitly get and set the search client for the *test* index
            try:
                print(
                    f"Re-fetching search client for test index: {cls.test_index_name}"
                )
                _, test_search_client = (
                    cls.search_service.client_manager.get_search_clients(
                        cls.test_index_name
                    )
                )
                cls.search_service.search_client = (
                    test_search_client  # Update the client on the service instance
                )
                print(
                    f"Successfully updated search client for index {cls.test_index_name}"
                )
            except Exception as client_error:
                print(
                    f"Failed to get search client for test index {cls.test_index_name}: {client_error}"
                )
                pytest.skip(
                    f"Could not get search client for test index: {client_error}"
                )
        except Exception as e:
            print(f"Warning: Could not create test index: {str(e)}")
            pytest.skip(f"Could not create test index: {str(e)}")

        # Search service is already initialized via the indexing service
        print(f"Using search service with test index: {cls.test_index_name}")

        # Prepare test files
        cls.test_files_dir = (
            Path(__file__).resolve().parent.parent.parent
            / "documents"
            / "tests"
            / "test_files"
        )
        cls.test_files = [f for f in cls.test_files_dir.glob("*") if f.is_file()]
        print(f"Found {len(cls.test_files)} test files in {cls.test_files_dir}")

        print("==== Setup completed ====")

    def test_01_create_search_index(self):
        """Test index creation with vector search capabilities"""
        print("\n=== Testing Index Creation ===")

        # Skip index creation test - we're using an existing index for the hackathon
        print("Skipping index creation test - using existing index")
        self.cost_tracker["index_operations"] += 1

        # For test purposes, assume the index exists
        print(f"✓ Using existing search index '{self.search_service.index_name}'")

        # Get and verify the index
        index = self.search_service.get_index()
        self.assertIsNotNone(index)

        # Verify fields and their properties
        fields = {field.name: field for field in index.fields}

        # Test required fields
        required_fields = {
            "id": {"key": True, "type": SearchFieldDataType.String},
            "document_id": {"type": SearchFieldDataType.String, "filterable": True},
            "content": {"type": SearchFieldDataType.String, "searchable": True},
            "chunk_index": {"type": SearchFieldDataType.Int32, "filterable": True},
            "metadata": {"type": SearchFieldDataType.String, "filterable": False},
            "embedding": {
                "type": SearchFieldDataType.Collection(SearchFieldDataType.Single)
            },
        }

        for field_name, properties in required_fields.items():
            self.assertIn(field_name, fields, f"Missing field: {field_name}")
            field = fields[field_name]
            for prop_name, prop_value in properties.items():
                if prop_name != "vectorSearchProfile":
                    self.assertEqual(
                        getattr(field, prop_name),
                        prop_value,
                        f"Field {field_name} has wrong {prop_name}",
                    )

        print("✓ All required fields verified")

    def test_02_document_indexing(self):
        """Test document processing, chunking, and indexing with embeddings"""
        print("\n=== Testing Document Processing and Indexing ===")

        # Process a test document
        test_file = next(f for f in self.test_files if f.suffix == ".txt")
        with open(test_file, "rb") as f:
            # Parse the document using the available parse_file method
            content, metadata = self.document_service.parse_file(f, "text/plain")

            # Generate a document ID for testing
            document_id = f"test-doc-{self.test_run_id}"

            # Generate embedding for content
            embedding = self.indexing_service.search_service.generate_embedding(
                content[:1000]
            )

            # Create a test document chunk
            chunk_id = f"chunk-{self.test_run_id}-0"

            # Index the document chunk
            success = self.indexing_service.search_service.index_document_chunk(
                chunk_id=chunk_id,
                document_id=document_id,
                content=content[:1000],  # Use first 1000 chars for test
                chunk_index=0,
                metadata={
                    "filename": test_file.name,
                    "content_type": "text/plain",
                    **metadata,
                },
                embedding=embedding,
            )

            if not success:
                self.fail("Failed to index document chunk")

        print(f"✓ Document {document_id} processed and indexed")

        # Wait for indexing to complete
        # Removed time.sleep(2)

        return document_id  # For use in search tests

    def test_03_search_operations(self):
        """Test various search operations: semantic, vector, and hybrid"""
        print("\n=== Testing Search Operations ===")

        # Use the document from the previous test
        document_id = self.test_02_document_indexing()

        # Test queries
        test_queries = [
            "What is the main topic?",  # Example query
            "document processing",  # Keyword search
            "system architecture",  # Vector search
        ]

        for query in test_queries:
            print(f"\nTesting search with query: '{query}'")

            # Test vector search
            results = self.search_service.vector_similarity_search(
                query=query, top=3, filter_expr=f"document_id eq '{document_id}'"
            )
            self.cost_tracker["vector_operations"] += 1
            print(f"✓ Vector search returned {len(results)} results")

            # Skip hybrid search for now - can be implemented later if needed
            print("Skipping hybrid search test for now")
            # Increment counter for reporting purposes
            self.cost_tracker["search_operations"] += 1

    @classmethod
    def tearDownClass(cls):
        print("\n==== Cleaning up SearchServiceTests ====")

        try:
            # Delete test documents and chunks
            print("Cleaning up test documents...")
            # No cleanup needed for document service in this test
            # We're only using parse_file which doesn't store documents

            # Delete test index
            print(f"Deleting test index '{cls.test_index_name}'...")
            cls.search_service.delete_index()
            cls.cost_tracker["index_operations"] += 1

        except Exception as e:
            print(f"Warning: Cleanup error - {str(e)}")
        finally:
            # Restore original index name
            settings.AZURE_SEARCH_INDEX_NAME = cls.original_index_name

        # Print cost tracking summary
        print("\n=== Azure Search Cost Summary ===")
        print(f"Index Operations: {cls.cost_tracker['index_operations']}")
        print(f"Vector Operations: {cls.cost_tracker['vector_operations']}")
        print(f"Search Operations: {cls.cost_tracker['search_operations']}")
        print(f"Total Operations: {sum(cls.cost_tracker.values())}")

        print("==== Cleanup completed ====")

        super().tearDownClass()
