import os
import unittest
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase
from django.core.exceptions import ValidationError
from io import BytesIO
from ..services.document_service import DocumentService
from ..models import Document, DocumentChunk

class TestDocumentService(TestCase):
    @patch.dict(os.environ, {
        'AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT': 'https://test-doc-intelligence.azure.com',
        'AZURE_STORAGE_ACCOUNT_URL': 'https://test-storage.azure.com',
        'AZURE_COGNITIVE_SEARCH_ENDPOINT': 'https://test-search.azure.com',
        'AZURE_SEARCH_INDEX_NAME': 'test-index',
        'AZURE_STORAGE_CONTAINER': 'test-container'
    })
    def setUp(self):
        self.document_service = DocumentService()
        # Mock Azure configurations after initialization
        self.document_service.azure = Mock()
        self.document_service.doc_intelligence_client = Mock()
        
        # Setup proper file mock
        self.test_file = BytesIO(b"test file content")
        self.test_file.name = "test_document.pdf"
        self.test_filename = "test_document.pdf"
        self.test_title = "Test Document"
        
    def mock_azure_response(self):
        # Mock Document Intelligence response
        mock_result = Mock()
        mock_result.paragraphs = [Mock(content="Test content paragraph 1."), 
                                 Mock(content="Test content paragraph 2.")]
        mock_poller = Mock()
        mock_poller.result.return_value = mock_result
        self.document_service.doc_intelligence_client.begin_analyze_document.return_value = mock_poller
        
        # Mock Azure Storage
        mock_container_client = Mock()
        self.document_service.azure.storage.get_container_client.return_value = mock_container_client
        
        # Mock Azure Search
        self.document_service.azure.search.upload_documents = Mock()
        
        return mock_result

    def test_process_document_success(self):
        self.mock_azure_response()
        
        # Reset file position before processing
        self.test_file.seek(0)
        
        # Execute
        document = self.document_service.process_document(
            self.test_file,
            self.test_filename,
            self.test_title
        )
        
        # Assert
        self.assertIsInstance(document, Document)
        self.assertEqual(document.title, self.test_title)
        self.assertEqual(document.file_type, "pdf")
        
        # Verify chunks were created
        chunks = DocumentChunk.objects.filter(document=document)
        self.assertTrue(chunks.exists())
        
        # Verify Azure services were called
        self.document_service.doc_intelligence_client.begin_analyze_document.assert_called_once()
        self.document_service.azure.storage.get_container_client.assert_called_once()
        self.document_service.azure.search.upload_documents.assert_called_once()

    def test_process_document_failure(self):
        # Mock Document Intelligence to raise an exception
        self.document_service.doc_intelligence_client.begin_analyze_document.side_effect = Exception("Test error")
        
        # Assert that ValidationError is raised
        with self.assertRaises(ValidationError):
            self.document_service.process_document(
                self.test_file,
                self.test_filename,
                self.test_title
            )

    def test_search_documents_success(self):
        # Mock search results
        mock_results = [
            {"id": "1_0", "content": "Test content", "score": 0.8},
            {"id": "1_1", "content": "More test content", "score": 0.6}
        ]
        self.document_service.azure.search.search.return_value = mock_results
        
        # Execute
        results = self.document_service.search_documents("test query")
        
        # Assert
        self.assertEqual(len(results), 2)
        self.document_service.azure.search.search.assert_called_once_with(
            search_text="test query",
            top=10,
            include_total_count=True
        )

    def test_search_documents_failure(self):
        # Mock search to raise an exception
        self.document_service.azure.search.search.side_effect = Exception("Search error")
        
        # Assert that ValidationError is raised
        with self.assertRaises(ValidationError):
            self.document_service.search_documents("test query")

if __name__ == '__main__':
    unittest.main()
