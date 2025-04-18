# Konveyor Test Errors

## Documents App

### test_document_service.py
1. API Change Errors:
   ```
   AttributeError: 'DocumentService' object has no attribute 'process_document'
   ```
   - Affects all tests using the old API
   - Need to update to use `parse_file` method

2. Document Processing Errors:
   ```
   TypeError: DocumentService.parse_file() got an unexpected keyword argument 'filename'
   ```
   - Tests are passing wrong parameters to parse_file
   - Need to update to only use file_obj and content_type

## Search App

### test_indexing_service.py
1. Embedding Field Errors:
   ```
   The request is invalid. Details: A null value was found for the property named 'embedding', which has the expected type 'Collection(Edm.Single)[Nullable=False]'
   ```
   - Index schema requires non-null embeddings
   - Need to ensure embedding generation works or update schema

2. Document Processing Errors:
   ```
   AttributeError: 'DocumentService' object has no attribute 'process_document'
   ```
   - Same API change issue as documents app
   - Need to update to use new API

3. Test Setup Errors:
   ```
   Dictionary-based index creation failed: Unable to get e_tag from the model
   ```
   - Index creation fallback to SearchIndex object works
   - But need to investigate e_tag issue

### test_search_service.py
1. Search Index Errors:
   ```
   Error indexing document chunk: The request is invalid. Details: A null value was found for the property named 'embedding'
   ```
   - Need to ensure embeddings are generated correctly
   - Or update schema to allow null embeddings

## Common Issues

1. Azure Service Configuration:
   - Some tests fail when Azure services are not properly configured
   - Need to ensure all required environment variables are set:
     ```
     AZURE_OPENAI_ENDPOINT
     AZURE_OPENAI_API_KEY
     AZURE_OPENAI_EMBEDDING_DEPLOYMENT
     AZURE_SEARCH_ENDPOINT
     AZURE_SEARCH_API_KEY
     AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT
     AZURE_DOCUMENT_INTELLIGENCE_API_KEY
     ```

2. Test Data Issues:
   - Some test files may not exist
   - Need to ensure test data is properly set up
   - Consider adding test data fixtures

## Next Actions

1. Update test_indexing_service.py:
   - Fix document processing to use new API
   - Add proper embedding generation
   - Update index schema handling

2. Update test_document_service.py:
   - Remove old API references
   - Update to use new parse_file method
   - Add proper document/chunk creation

3. Update test_search_service.py:
   - Fix embedding generation
   - Update index schema handling
   - Add better error handling
