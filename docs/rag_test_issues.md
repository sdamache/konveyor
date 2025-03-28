# RAG Integration Test Issues

## Current Test Case: `test_kubernetes_basic_concepts`

### 1. Azure OpenAI Model Configuration Issues

#### Problem
- Test is failing with error: `OperationNotSupported - The embeddings operation does not work with the specified model, gpt-4o`
- The system is trying to use an incorrect model for embeddings

#### Current Configuration
```
AZURE_OPENAI_API_KEY=********(set correctly only)
AZURE_OPENAI_ENDPOINT=https://eastus.api.cognitive.microsoft.com/
AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-deployment
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002
```

#### Code Areas Affected
1. `konveyor/core/azure/clients.py`:
   - OpenAI client initialization
   - Currently not specifying deployment at client level (correct)

2. `konveyor/apps/search/services/search_service.py`:
   - Embedding generation logic
   - Has duplicate code blocks for embedding generation
   - Not properly using the deployment name from environment variables

### 2. Django Configuration

#### Problem
- Django settings need to be properly configured before model imports
- Currently using development settings from `konveyor/settings/development.py`

### 3. Test Structure Issues

1. **Setup Phase**:
   ```python
   @pytest_asyncio.fixture(autouse=True)
   async def setup(self):
       # Fails at IndexingService initialization
       self.indexing_service = IndexingService()
   ```

2. **Service Dependencies**:
   - IndexingService depends on SearchService
   - SearchService depends on OpenAI client for embeddings
   - Document processing and storage dependencies

## Next Steps

1. **OpenAI Integration**:
   - Verify Azure OpenAI service has the correct model deployments
   - Ensure embedding deployment is properly configured
   - Clean up duplicate embedding generation code

2. **Test Environment**:
   - Set up proper test environment variables
   - Consider using test-specific settings
   - Add proper cleanup in test teardown

3. **Service Initialization**:
   - Review service initialization order
   - Consider mocking services for unit tests
   - Add better error handling and logging

## Required Azure OpenAI Deployments

1. **Chat Model**:
   - Purpose: Generating chat responses
   - Environment Variable: `AZURE_OPENAI_CHAT_DEPLOYMENT`
   - Default Value: 'gpt-35-turbo'

2. **Embedding Model**:
   - Purpose: Generating vector embeddings for search
   - Environment Variable: `AZURE_OPENAI_EMBEDDING_DEPLOYMENT`
   - Default Value: 'text-embedding-ada-002'
   - Status: Currently failing
