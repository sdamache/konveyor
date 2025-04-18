# Document Service Testing

This directory contains integration tests for the Konveyor document processing functionality. These tests connect to actual Azure services to validate the real-world functionality of the system.

## Testing Philosophy

In Konveyor, we prioritize real-world testing over mock-based testing. This approach ensures:

1. **Genuine Service Integration**: Our tests validate actual interactions with Azure services
2. **Production-Like Behavior**: Tests run against the same services used in production
3. **Complete Validation**: End-to-end workflows are tested from document upload to search retrieval

## Test Files

1. **test_document_service.py**: End-to-end tests that use real Azure services to validate the document processing pipeline

## Prerequisites

You must have:
- Active Azure services (Document Intelligence, Blob Storage, Cognitive Search, OpenAI)
- Required environment variables set

See [README_DETAILED.md](./README_DETAILED.md) for detailed requirements.

## Running Tests

```bash
# From the project root
./konveyor/apps/documents/tests/run_tests.sh

# Or directly with Django
python manage.py test konveyor.apps.documents.tests.test_document_service
```

## Test Coverage

The tests cover the following key functionalities:

1. **Document Upload and Processing**
   - Uploading text documents
   - Processing documents through Azure Document Intelligence
   - Extracting content and generating chunks
   - Verifying chunks are properly created

2. **PDF Document Processing**
   - Processing PDF documents with Azure Document Intelligence
   - Validating special handling for PDF files

3. **Search Functionality**
   - Indexing documents in Azure Cognitive Search
   - Performing semantic searches against the index
   - Retrieving and validating search results

4. **End-to-End Workflow**
   - Complete document processing and search pipeline
   - Testing with unique identifiers to ensure precise results
   - Validating the entire system works together

## Test Isolation

Each test run uses a unique identifier to ensure:
1. Tests from different runs don't interfere with each other
2. All test artifacts can be easily identified and cleaned up
3. Search queries can be targeted to specific test documents

## Best Practices

1. **Run Tests Before Deployment**: Always run integration tests before deploying changes
2. **Keep Tests Current**: Update tests when Azure service interfaces change
3. **Test Critical Workflows**: Prioritize tests for user-facing functionality
4. **Maintain Test Data**: Keep test files updated and realistic
5. **Clean Up After Tests**: The teardown process removes created resources

## Debugging Test Failures

See [README_DETAILED.md](./README_DETAILED.md) for detailed troubleshooting tips.

## Important Notes

- These tests will incur Azure service usage costs
- Tests may take significant time to run due to document processing and indexing delays
- Never run these tests against production Azure resources unless you're absolutely sure of what you're doing 