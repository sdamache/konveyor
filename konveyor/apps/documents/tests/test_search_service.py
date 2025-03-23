from django.test import TestCase
from django.conf import settings
from ..services.search_service import SearchService
from azure.search.documents.indexes.models import SearchIndex

class SearchServiceTests(TestCase):
    def setUp(self):
        self.search_service = SearchService()

    def test_create_search_index(self):
        # Create the index
        index = self.search_service.create_search_index()
        
        # Verify the index was created
        self.assertIsInstance(index, SearchIndex)
        self.assertEqual(index.name, settings.AZURE_SEARCH_INDEX_NAME)
        
        # Verify fields
        field_names = [field.name for field in index.fields]
        expected_fields = ['id', 'document_id', 'content', 'chunk_index', 
                         'metadata', 'created_at', 'file_type']
        for field in expected_fields:
            self.assertIn(field, field_names)

    def test_get_index(self):
        # Create the index first
        self.search_service.create_search_index()
        
        # Get the index
        index = self.search_service.get_index()
        
        # Verify we can get the index
        self.assertIsInstance(index, SearchIndex)
        self.assertEqual(index.name, settings.AZURE_SEARCH_INDEX_NAME)

    def tearDown(self):
        # Clean up - delete the test index
        try:
            self.search_service.delete_index()
        except:
            pass 