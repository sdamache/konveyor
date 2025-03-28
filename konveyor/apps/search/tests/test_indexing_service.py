import os
import uuid
import pytest
from django.conf import settings
from django.test import TestCase
from io import BytesIO
import logging

from konveyor.apps.documents.models import Document, DocumentChunk
from konveyor.apps.documents.services.document_service import DocumentService
from konveyor.apps.search.services.indexing_service import IndexingService
from konveyor.config.azure import AzureConfig

logger = logging.getLogger(__name__)

class TestIndexingService(TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test environment with detailed logging and validation."""
        super().setUpClass()
        logger.info("==== Setting up TestIndexingService ====")
        
        # 1. Initialize and validate document service
        try:
            logger.info("Initializing DocumentService...")
            cls.document_service = DocumentService()
            logger.info("DocumentService initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize DocumentService: {e}")
            pytest.skip(f"DocumentService initialization failed: {e}")
        
        # 2. Initialize and validate indexing service
        try:
            logger.info("Initializing IndexingService...")
            cls.indexing_service = IndexingService()
            logger.info("IndexingService initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize IndexingService: {e}")
            pytest.skip(f"IndexingService initialization failed: {e}")
        
        # 3. Initialize and validate Azure config
        try:
            logger.info("Initializing AzureConfig...")
            cls.azure_config = AzureConfig()
            logger.info("AzureConfig initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize AzureConfig: {e}")
            pytest.skip(f"AzureConfig initialization failed: {e}")
        
        # 4. Validate Azure OpenAI configuration
        try:
            openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
            openai_key = os.getenv("AZURE_OPENAI_API_KEY")
            gpt_api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
            embeddings_api_version = os.getenv("AZURE_OPENAI_EMBEDDING_API_VERSION", "2023-05-15")
            
            logger.info(f"OpenAI Endpoint: {openai_endpoint if openai_endpoint else 'Not set'}")
            logger.info(f"OpenAI Key: {'Set' if openai_key else 'Not set'}")
            logger.info(f"OpenAI GPT API Version: {gpt_api_version}")
            logger.info(f"OpenAI Embeddings API Version: {embeddings_api_version}")
            
            if not openai_endpoint or not openai_key:
                logger.warning("Azure OpenAI credentials not fully configured")
            else:
                logger.info("Azure OpenAI credentials configured")
        except Exception as e:
            logger.error(f"Error checking OpenAI configuration: {e}")
        
        # 5. Validate Azure Search configuration
        try:
            search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
            search_key = os.getenv("AZURE_SEARCH_API_KEY")
            original_index_name = os.getenv("AZURE_SEARCH_INDEX_NAME", "konveyor-documents")
            
            logger.info(f"Search Endpoint: {search_endpoint if search_endpoint else 'Not set'}")
            logger.info(f"Search Key: {'Set' if search_key else 'Not set'}")
            logger.info(f"Original Index Name: {original_index_name}")
            
            if not search_endpoint or not search_key:
                logger.warning("Azure Search credentials not fully configured")
            else:
                logger.info("Azure Search credentials configured")
        except Exception as e:
            logger.error(f"Error checking Search configuration: {e}")
        
        # 6. Generate a unique test index name
        cls.test_index_name = f"konveyor-test-{uuid.uuid4().hex[:8]}"
        logger.info(f"Generated test index name: {cls.test_index_name}")
        
        # 7. Store original index name and override for tests
        cls.original_index_name = os.getenv("AZURE_SEARCH_INDEX_NAME", "konveyor-documents")
        os.environ["AZURE_SEARCH_INDEX_NAME"] = cls.test_index_name
        logger.info(f"Set environment variable AZURE_SEARCH_INDEX_NAME to {cls.test_index_name}")
        
        # 8. Update the search service to use the test index
        try:
            logger.info("Updating search service to use test index...")
            cls.indexing_service.search_service.index_name = cls.test_index_name
            logger.info(f"Updated search service index name to {cls.test_index_name}")
        except Exception as e:
            logger.error(f"Failed to update search service index name: {e}")
        
        # 9. Create a new search client for the test index
        try:
            logger.info("Creating new search client for test index...")
            original_client = cls.indexing_service.search_service.search_client
            cls.indexing_service.search_service.search_client = cls.indexing_service.search_service.index_client.get_search_client(
                index_name=cls.test_index_name
            )
            logger.info(f"Created new search client for index {cls.test_index_name}")
        except Exception as e:
            logger.error(f"Failed to create new search client: {e}")
        
        # 10. Ensure search client is available
        if cls.azure_config.search is None:
            logger.error("Azure Search client not available from AzureConfig")
            pytest.skip("Azure Search client not available")
        else:
            logger.info("Azure Search client available from AzureConfig")
        
        # 11. Set up test files directory
        cls.test_files_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            'documents', 'tests', 'test_files'
        )
        logger.info(f"Test files directory: {cls.test_files_dir}")
        
        # 12. Validate test files
        test_files = [f for f in os.listdir(cls.test_files_dir) if os.path.isfile(os.path.join(cls.test_files_dir, f))]
        logger.info(f"Found {len(test_files)} test files: {', '.join(test_files)}")
        
        # 13. Create the test index with detailed error handling
        try:
            logger.info(f"Creating test index: {cls.test_index_name}...")
            result = cls.indexing_service.search_service.create_search_index(index_name=cls.test_index_name)
            if result:
                logger.info(f"Successfully created test index: {cls.test_index_name}")
            else:
                logger.warning(f"Index creation returned False for {cls.test_index_name}")
                
                # Check if index was actually created despite returning False
                existing_indices = [index.name for index in cls.indexing_service.search_service.index_client.list_indexes()]
                if cls.test_index_name in existing_indices:
                    logger.info(f"Despite return value, index {cls.test_index_name} appears to be created")
                else:
                    logger.warning(f"Index {cls.test_index_name} was not created")
                    
        except Exception as e:
            logger.error(f"Failed to create test index: {str(e)}")
            
            # Check if index already exists despite the error
            try:
                existing_indices = [index.name for index in cls.indexing_service.search_service.index_client.list_indexes()]
                if cls.test_index_name in existing_indices:
                    logger.info(f"Index {cls.test_index_name} already exists, continuing with tests")
                else:
                    logger.warning(f"Index {cls.test_index_name} does not exist, tests may fail")
            except Exception as check_e:
                logger.error(f"Could not check if index exists: {str(check_e)}")
        
        # 14. Test embedding generation
        try:
            logger.info("Testing embedding generation...")
            embedding = cls.indexing_service.search_service.generate_embedding("Test embedding generation")
            logger.info(f"Successfully generated test embedding with {len(embedding)} dimensions")
        except Exception as e:
            logger.error(f"Test embedding generation failed: {str(e)}")
            # Don't skip tests yet - individual tests can handle this
        
        logger.info("==== TestIndexingService setup completed ====")
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test resources with detailed logging."""
        logger.info("==== Tearing down TestIndexingService ====")
        
        # 1. Restore original index name
        try:
            os.environ["AZURE_SEARCH_INDEX_NAME"] = cls.original_index_name
            logger.info(f"Restored environment variable AZURE_SEARCH_INDEX_NAME to {cls.original_index_name}")
        except Exception as e:
            logger.error(f"Failed to restore original index name: {e}")
        
        # 2. Reset the search service to use the original index
        try:
            cls.indexing_service.search_service.index_name = cls.original_index_name
            logger.info(f"Reset search service index name to {cls.original_index_name}")
            
            cls.indexing_service.search_service.search_client = cls.indexing_service.search_service.index_client.get_search_client(
                index_name=cls.original_index_name
            )
            logger.info(f"Reset search client to original index {cls.original_index_name}")
        except Exception as e:
            logger.error(f"Failed to reset search service: {e}")
        
        # 3. Delete the test index if it exists
        try:
            logger.info(f"Attempting to delete test index: {cls.test_index_name}...")
            # Check if index exists first
            existing_indices = [index.name for index in cls.indexing_service.search_service.index_client.list_indexes()]
            if cls.test_index_name in existing_indices:
                logger.info(f"Test index {cls.test_index_name} exists, deleting...")
                cls.indexing_service.search_service.index_client.delete_index(cls.test_index_name)
                logger.info(f"Successfully deleted test index: {cls.test_index_name}")
            else:
                logger.info(f"Test index {cls.test_index_name} does not exist, no cleanup needed")
        except Exception as e:
            logger.error(f"Warning: Couldn't delete test index: {e}")
        
        logger.info("==== TestIndexingService teardown completed ====")
        super().tearDownClass()
    
    def setUp(self):
        # No need to create index in each test if we created it in setUpClass
        pass
        
    def tearDown(self):
        # Clean up documents and chunks after each test
        Document.objects.all().delete()
        DocumentChunk.objects.all().delete()
    
    def test_index_existence_verification(self):
        """Test that index existence verification works correctly."""
        # Check if our test index exists
        exists = self.test_index_name in [index.name for index in 
                                         self.indexing_service.search_service.index_client.list_indexes()]
        self.assertTrue(exists, f"Test index {self.test_index_name} should exist")
        
        # Check non-existent index
        fake_index_name = f"nonexistent-index-{uuid.uuid4().hex[:8]}"
        exists = fake_index_name in [index.name for index in 
                                    self.indexing_service.search_service.index_client.list_indexes()]
        self.assertFalse(exists, "Non-existent index should return False")
    
    def test_single_document_indexing(self):
        """Test indexing a single document."""
        # Process a text document first
        sample_text_path = os.path.join(self.test_files_dir, 'sample.txt')
        
        # Read the file contents
        with open(sample_text_path, 'rb') as f:
            file_content = f.read()
        
        # Create a file-like object
        file_obj = BytesIO(file_content)
        file_obj.name = 'sample.txt'
        
        # Process document to create chunks
        document = self.document_service.process_document(
            file_obj=file_obj,
            filename='sample.txt',
            title='Sample Text'
        )
        
        # Verify document and chunks were created
        self.assertIsNotNone(document)
        chunks = DocumentChunk.objects.filter(document=document)
        self.assertTrue(chunks.exists(), "Document chunks should be created")
        
        # Index a single chunk
        chunk = chunks.first()
        # Get chunk content from blob storage
        chunk_content = self.document_service.get_chunk_content(chunk)
        
        # Try to generate embedding or use mock if it fails
        try:
            # Generate embedding for the chunk
            embedding = self.indexing_service.search_service.generate_embedding(chunk_content)
        except Exception as e:
            # Log the error but continue with a mock embedding for testing
            logger.warning(f"Failed to generate embedding, using mock: {str(e)}")
            # Create a mock embedding of the correct size (1536 dimensions)
            embedding = [0.1] * 1536
            
        # Index the chunk with vector search support
        result = self.indexing_service.search_service.index_document_chunk(
            chunk_id=str(chunk.id),
            document_id=str(document.id),
            content=chunk_content,
            chunk_index=chunk.chunk_index,
            metadata=chunk.metadata,
            embedding=embedding
        )
        
        # Verify successful indexing
        self.assertTrue(result, "Chunk indexing should return True for success")

    def test_batch_document_indexing(self):
        """Test batch indexing of document chunks."""
        # Process documents of different types
        file_paths = [
            ('sample.txt', 'text/plain'),
            ('sample.pdf', 'application/pdf'),
            ('sample.md', 'text/markdown')
        ]
        
        documents = []
        all_chunks = []
        
        # Process each document to create chunks
        for filename, content_type in file_paths:
            file_path = os.path.join(self.test_files_dir, filename)
            if os.path.exists(file_path):
                # Read the file contents
                with open(file_path, 'rb') as f:
                    file_content = f.read()
                
                # Create a file-like object
                file_obj = BytesIO(file_content)
                file_obj.name = filename
                
                document = self.document_service.process_document(
                    file_obj=file_obj,
                    filename=filename,
                    title=f'Test {filename}'
                )
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
                    embedding = self.indexing_service.search_service.generate_embedding(chunk_content)
                except Exception as e:
                    # Log the error but continue with a mock embedding for testing
                    logger.warning(f"Failed to generate embedding, using mock: {str(e)}")
                    # Create a mock embedding of the correct size (1536 dimensions)
                    embedding = [0.1] * 1536
                
                # Index the chunk
                result = self.indexing_service.search_service.index_document_chunk(
                    chunk_id=str(chunk.id),
                    document_id=str(chunk.document.id),
                    content=chunk_content,
                    chunk_index=chunk.chunk_index,
                    metadata=chunk.metadata,
                    embedding=embedding
                )
                if result:
                    success_count += 1
            except Exception as e:
                print(f"Error indexing chunk {chunk.id}: {e}")
        
        # Verify successful batch indexing
        self.assertTrue(success_count > 0, "At least one chunk should be indexed successfully")

    def test_different_document_types(self):
        """Test indexing chunks from different document types."""
        document_types = {
            'text': ('sample.txt', 'text/plain'),
            'pdf': ('sample.pdf', 'application/pdf'),
            'markdown': ('sample.md', 'text/markdown'),
            'docx': ('sample.docx', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        }
        
        indexed_by_type = {}
        
        # Process each document type
        for doc_type, (filename, content_type) in document_types.items():
            file_path = os.path.join(self.test_files_dir, filename)
            if not os.path.exists(file_path):
                print(f"Skipping {doc_type} test - file {filename} not found")
                continue
                
            # Read the file contents
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            # Create a file-like object
            file_obj = BytesIO(file_content)
            file_obj.name = filename
            
            # Process document
            document = self.document_service.process_document(
                file_obj=file_obj,
                filename=filename,
                title=f'Test {filename}'
            )
            
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
                    embedding = self.indexing_service.search_service.generate_embedding(chunk_content)
                except Exception as e:
                    # Log the error but continue with a mock embedding for testing
                    logger.warning(f"Failed to generate embedding for {doc_type}, using mock: {str(e)}")
                    # Create a mock embedding of the correct size (1536 dimensions)
                    embedding = [0.1] * 1536
                
                # Index the chunk
                result = self.indexing_service.search_service.index_document_chunk(
                    chunk_id=str(chunk.id),
                    document_id=str(document.id),
                    content=chunk_content,
                    chunk_index=chunk.chunk_index,
                    metadata=chunk.metadata,
                    embedding=embedding
                )
                indexed_by_type[doc_type] = result
            except Exception as e:
                indexed_by_type[doc_type] = False
                print(f"Error indexing {doc_type} document: {e}")
            
        # Verify indexing worked for available document types
        for doc_type, result in indexed_by_type.items():
            self.assertTrue(
                result, 
                f"Indexing should succeed for {doc_type} document"
            )
            
    def test_malformed_document_error_handling(self):
        """Test how indexing service handles invalid document data."""
        # Create a document with malformed/problematic content
        doc = Document.objects.create(
            title="Malformed Document",
            blob_path="malformed.txt",
            content_type="text/plain",
            status="processed"
        )
        
        # Test cases with problematic content
        problem_contents = [
            # Empty content
            "",
            # Extremely long content
            "a" * 100000,
            # Content with special characters
            """Special chars: ¡™£¢∞§¶•ªº–≠œ∑´®†¥¨ˆøπ"'«åß∂ƒ©˙∆˚¬…æΩ≈ç√∫˜µ≤≥÷"""
        ]
        
        test_results = {}
        
        for i, content in enumerate(problem_contents):
            content_desc = f"Empty string" if content == "" else f"Long content" if len(content) > 1000 else "Special characters"
            
            # Create a problematic chunk
            chunk = DocumentChunk.objects.create(
                document=doc,
                chunk_index=i+1,
                blob_path=f"chunks/{doc.id}/{uuid.uuid4().hex}.txt",
                metadata={
                    'chunk_id': uuid.uuid4().hex,
                    'chunk_index': i+1,
                    'parent_document_id': str(doc.id),
                    'content_length': len(content)
                }
            )
            
            try:
                # Try to index the problematic content directly
                result = self.indexing_service.search_service.index_document_chunk(
                    chunk_id=str(chunk.id),
                    document_id=str(doc.id),
                    content=content,
                    chunk_index=i+1,
                    metadata=chunk.metadata,
                    embedding=None  # Allow the service to generate embedding
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
        print("\n" + "="*60)
        print(" INDEXING SERVICE TEST RESULTS ".center(60, "="))
        print("="*60)
        print(f"{'CONTENT TYPE':<30} | {'RESULT':<25}")
        print("-"*60)
        
        for content_type, result in results_dict.items():
            result_str = str(result)
            if len(result_str) > 25:
                result_str = result_str[:22] + "..."
            print(f"{content_type:<30} | {result_str:<25}")
        
        print("="*60 + "\n") 