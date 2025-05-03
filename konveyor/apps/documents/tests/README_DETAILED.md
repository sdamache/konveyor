# Konveyor Document Service Testing - Detailed Guide

This document provides detailed information for running the document service tests in Konveyor. These tests connect to **actual Azure services** to validate the real-world functionality of the system.

## Prerequisites

Before running the tests, you must have:

1. **Azure Services**: Active Azure services with appropriate access
   - Azure Document Intelligence
   - Azure Blob Storage
   - Azure Cognitive Search
   - Azure OpenAI (for embeddings)

2. **Environment Variables**: The following environment variables must be set:
   ```
   AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://your-doc-intel.cognitiveservices.azure.com
   AZURE_DOCUMENT_INTELLIGENCE_KEY=your-doc-intel-key
   AZURE_STORAGE_CONNECTION_STRING=your-storage-connection-string
   AZURE_STORAGE_CONTAINER_NAME=your-container-name
   AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com
   AZURE_OPENAI_API_KEY=your-openai-key
   AZURE_OPENAI_API_VERSION=2023-12-01-preview
   AZURE_SEARCH_ENDPOINT=https://your-search.search.windows.net
   AZURE_SEARCH_API_KEY=your-search-key
   AZURE_SEARCH_INDEX_NAME=your-search-index
   ```

3. **Test Files**: Sample text or PDF files in the `test_files` directory

## Setting Up Environment Variables

For convenience, you can create a `.env` file in the project root directory with all the required variables and source it before running tests:

```bash
# Create a .env file (don't commit this to version control)
cat > .env << EOF
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://your-doc-intel.cognitiveservices.azure.com
AZURE_DOCUMENT_INTELLIGENCE_KEY=your-doc-intel-key
AZURE_STORAGE_CONNECTION_STRING=your-storage-connection-string
AZURE_STORAGE_CONTAINER_NAME=your-container-name
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com
AZURE_OPENAI_API_KEY=your-openai-key
AZURE_OPENAI_API_VERSION=2023-12-01-preview
AZURE_SEARCH_ENDPOINT=https://your-search.search.windows.net
AZURE_SEARCH_API_KEY=your-search-key
AZURE_SEARCH_INDEX_NAME=your-search-index
EOF

# Source the environment variables
source .env
```

## Running Tests

To run all tests:

```bash
# From the project root
./konveyor/apps/documents/tests/run_tests.sh
```

To run a specific test:

```bash
# Run a specific test method
python manage.py test konveyor.apps.documents.tests.test_document_service.TestDocumentServiceIntegration.test_01_document_upload_and_processing
```

You can also use the script with options:

```bash
# Run with increased verbosity
./konveyor/apps/documents/tests/run_tests.sh -v=2

# Run specific test
./konveyor/apps/documents/tests/run_tests.sh -t=test_01_document_upload_and_processing
```

## Test Process

The tests perform the following:

1. **Document Upload**: Uploads a text document to Azure Blob Storage
2. **Document Processing**: Processes the document through Azure Document Intelligence
3. **Chunking**: Tests the document chunking functionality
4. **Search Indexing**: Verifies documents are properly indexed in Azure Cognitive Search
5. **Search Retrieval**: Tests searching for documents with specific content
6. **End-to-End Workflow**: Validates the complete document processing pipeline

## Understanding Test Results

The tests are designed to be verbose and will output progress information, including:

- A unique test run ID that identifies documents created during this test run
- The number of chunks created for each document
- Search results details
- Cleanup information

Example output:

```
Integration test run ID: 12345678

Testing text document upload and processing...
Document processed successfully with 3 chunks

Testing PDF document processing with Document Intelligence...
PDF document processed successfully with 5 chunks

Testing search functionality with actual Azure Cognitive Search...
Searching for: 'test 12345678'
Received 2 search results
Top result snippet: This is a test document for Konveyor integration test 12345678...

Testing end-to-end document workflow...
E2E document created with 2 chunks
Waiting for document indexing to complete...
Searching for unique term: 'UniqueIdentifier12345678'
E2E test successful - found 1 results for unique search term

Cleaning up test documents...
Deleting document: Text Test 12345678
Deleting document: PDF Test 12345678
Deleting document: E2E Test 12345678
```

## Troubleshooting

If tests fail, check:

1. **Environment Variables**: Verify all variables are set correctly
2. **Azure Service Status**: Ensure all Azure services are operational
3. **Permissions**: Confirm your credentials have appropriate permissions
4. **Container Existence**: Verify the blob container exists in your storage account
5. **Search Index**: Ensure the search index is properly configured with vector search capability
6. **Test Files**: Check that sample test files exist in the appropriate directory

Common failures and solutions:

| Error | Possible Solution |
|-------|-------------------|
| `Missing environment variable` | Set the environment variable or source your `.env` file |
| `Container not found` | Create the container in Azure Blob Storage |
| `Search index doesn't exist` | Create the index in Azure Cognitive Search |
| `Authentication failed` | Check your API keys and credentials |
| `Rate limit exceeded` | Reduce test frequency or contact Azure support to increase limits |
| `Document processing failed` | Check if the document format is supported by Document Intelligence |

## Adding New Tests

When adding new tests:

1. Add them to the `TestDocumentServiceIntegration` class in `test_document_service.py`
2. Prefix test methods with numbers to control execution order (e.g., `test_01_...`)
3. Include the test run ID in document titles and content for isolation
4. Add appropriate cleanup logic to avoid cluttering Azure services

## Security Best Practices

1. **Never commit API keys or secrets** to the repository
2. Use environment variables or Azure Key Vault for credentials
3. Use separate Azure resources for testing versus production
4. Clean up test resources after tests complete
5. Use the minimum necessary permissions for test accounts

## Cost Management

These tests use real Azure services and may incur costs. To minimize expenses:

1. Run tests only when necessary (e.g., before releases or after significant changes)
2. Use the smallest document sizes that can validate functionality
3. Choose lower-tier Azure services for testing environments
4. Ensure proper cleanup of resources after tests
5. Consider setting up Azure spending limits or alerts

## Continuous Integration

To include these tests in CI pipelines:

1. Store required credentials securely in CI system secrets
2. Run tests selectively on important branches (e.g., main, release)
3. Consider separating fast unit tests from these longer integration tests
4. Set up proper timeouts as document processing and indexing can take time
