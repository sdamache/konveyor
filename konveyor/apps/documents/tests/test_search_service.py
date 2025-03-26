from django.test import TestCase
from django.conf import settings
# Use explicit imports to avoid confusion
from konveyor.apps.documents.services.search_service import SearchService
from azure.search.documents.indexes.models import SearchIndex, SearchFieldDataType  # Azure's documents module
import json

class SearchServiceTests(TestCase):
    def setUp(self):
        # Modify settings before creating SearchService
        self.original_index_name = settings.AZURE_SEARCH_INDEX_NAME
        settings.AZURE_SEARCH_INDEX_NAME = f"test-{settings.AZURE_SEARCH_INDEX_NAME}"
        # Create service after settings modification
        self.search_service = SearchService()
        
    def test_create_search_index(self):
        # Create the index
        index = self.search_service.create_search_index()
        
        # Verify the index was created
        self.assertIsInstance(index, SearchIndex)
        self.assertEqual(index.name, self.search_service.index_name)  # Use service's index_name
        
        # Verify fields and their properties
        fields = {field.name: field for field in index.fields}
        
        # Test id field
        self.assertTrue(fields['id'].key)
        self.assertEqual(fields['id'].type, SearchFieldDataType.String)
        
        # Test content field
        self.assertTrue(fields['content'].searchable)
        self.assertEqual(fields['content'].analyzer_name, 'standard.lucene')
        
        # Test metadata field
        self.assertTrue(fields['metadata'].filterable)
        
        # Test file_type field
        self.assertTrue(fields['file_type'].facetable)
        self.assertTrue(fields['file_type'].filterable)

    def test_index_operations(self):
        """Test the full lifecycle of an index: create, retrieve, delete, and verify deletion"""
        # Create index
        index = self.search_service.create_search_index()
        self.assertIsNotNone(index)
        print(f"\nℹ️ Test index '{index.name}' created successfully")
        
        # Get index and verify
        retrieved_index = self.search_service.get_index()
        self.assertEqual(retrieved_index.name, self.search_service.index_name)
        print(f"✓ Retrieved index '{retrieved_index.name}' matches created index")
        
        # Delete index and verify it's gone
        self.search_service.delete_index()
        print(f"🗑️ Index '{index.name}' deleted successfully")
        
        # Verify index is deleted by checking if get_index raises an exception
        print(f"Attempting to retrieve deleted index (expecting 'not found' error)...")
        with self.assertRaises(Exception) as context:
            self.search_service.get_index()
        print(f"✓ Test passed: Index not found (as expected)")

    def test_index_field_types(self):
        index = self.search_service.create_search_index()
        fields = {field.name: field for field in index.fields}
        
        # Verify specific field types
        self.assertEqual(fields['chunk_index'].type, SearchFieldDataType.Int32)
        self.assertEqual(fields['created_at'].type, SearchFieldDataType.DateTimeOffset)
        self.assertTrue(fields['created_at'].sortable)

    def tearDown(self):
        try:
            # Clean up - delete the test index
            self.search_service.delete_index()
        except:
            pass
        finally:
            # Restore original index name
            settings.AZURE_SEARCH_INDEX_NAME = self.original_index_name 