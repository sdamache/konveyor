# Konveyor Project Restructuring

## 1. Document Service Restructuring

### Current Organization

We have successfully reorganized the document service code:

```
konveyor/
├── core/
│   └── azure/              # Common Azure utilities
│       ├── mixins.py       # Shared service mixins
│       └── config.py       # Basic configuration
├── services/
│   └── documents/          # Core document service
│       ├── document_service.py
│       └── tests/
├── apps/
    └── documents/          # Django-specific handling
        ├── services/
        │   └── document_adapter.py
        └── tests/
```

### Key Improvements Made
- Separated core document processing from Django-specific code
- Moved Azure-specific code to appropriate locations
- Improved test organization
- Added proper error handling and retries

## 2. Further Directory Structure Analysis

### Current Issues

1. **Duplicate Services Directory**
   - We have two overlapping `services/` directories:
     ```
     ├── services/         # Core services
     │   └── documents/
     ├── services/         # Core business logic
     │   ├── documents/
     │   └── rag/
     ```
   - This creates confusion about where to place new services
   - Duplicates document service code

2. **Scattered RAG Implementation**
   - RAG-related code is spread across multiple locations:
     ```
     ├── apps/rag/        # Django interface
     ├── services/azure/  # RAG templates
     └── services/rag/    # Core implementation
     ```
   - Makes it difficult to understand the complete RAG system
   - Potential for duplicate functionality

3. **Azure Code Organization**
   - Azure-related code exists in multiple places:
     ```
     ├── core/azure/     # Common utilities
     ├── services/azure/ # Service implementations
     ```
   - Need clearer separation between common utilities and service-specific code

### Proposed Improvements

1. **Consolidate Services Directory**:
   ```
   konveyor/
   ├── services/         # All core services
   │   ├── documents/    # Document processing
   │   ├── rag/         # RAG implementation
   │   └── azure/       # Azure services
   ```

2. **Reorganize RAG Components**:
   ```
   konveyor/
   ├── services/
   │   └── rag/
   │       ├── core/           # Core RAG logic
   │       ├── templates/      # Prompt templates
   │       └── integrations/   # Azure/OpenAI integration
   └── apps/
       └── rag/              # Django interface
   ```

3. **Clarify Azure Organization**:
   ```
   konveyor/
   ├── core/
   │   └── azure/         # Framework utilities
   │       ├── config/
   │       └── mixins/
   └── services/
       └── azure/         # Service implementations
           ├── openai/
           ├── storage/
           └── document/
   ```

### Implementation Plan

1. **Phase 1: Service Consolidation**
   - Merge duplicate service directories
   - Update imports and references
   - Ensure tests pass after consolidation

2. **Phase 2: RAG Reorganization**
   - Move RAG components to new structure
   - Update RAG-related imports
   - Add integration tests for RAG system

3. **Phase 3: Azure Restructuring**
   - Reorganize Azure code by functionality
   - Update Azure service imports
   - Add documentation for Azure organization

### Benefits

- Clearer code organization
- Reduced duplication
- Better separation of concerns
- Easier to understand system components
- More maintainable codebase

This restructuring will follow the same successful pattern we used for the document service, maintaining backward compatibility while improving code organization.

## Directory Structure

We have reorganized the document service code to improve maintainability and separation of concerns:

```
konveyor/
├── core/
│   └── azure/              # Core Azure functionality
│       ├── mixins.py       # Common Azure service mixins
│       └── config.py       # Azure configuration utilities
├── services/
│   └── documents/          # Core document service
│       ├── document_service.py
│       └── tests/
└── apps/
    └── documents/          # Django-specific document handling
        ├── services/
        │   └── document_adapter.py
        └── tests/
```

## Key Components

1. **Core Document Service** (`services/documents/document_service.py`):
   - Framework-agnostic implementation
   - Uses Azure Document Intelligence for parsing
   - Supports multiple document formats (PDF, DOCX, Markdown, Text)
   - Configurable through environment variables:
     - `AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT`
     - `AZURE_DOCUMENT_INTELLIGENCE_API_KEY`
     - `AZURE_DOCUMENT_INTELLIGENCE_MODEL` (optional)

2. **Django Adapter** (`apps/documents/services/document_adapter.py`):
   - Adapts core service for Django integration
   - Handles Django-specific file objects
   - Delegates core processing to DocumentService
   - Uses `__getattr__` for transparent method delegation

3. **Azure Integration**:
   - Moved Azure-specific code to `core/azure`
   - Common mixins for logging and client initialization
   - Improved error handling and retries

## Testing Structure

1. **Core Service Tests** (`services/documents/tests/`):
   - Tests core document processing functionality
   - Uses actual files for realistic testing
   - Skips tests if Azure credentials are missing

2. **Django Integration Tests** (`apps/documents/tests/`):
   - Tests Django-specific adapter functionality
   - Validates proper delegation to core service
   - Includes error handling scenarios

## Environment Configuration

Required environment variables:
```shell
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=<your-endpoint>
AZURE_DOCUMENT_INTELLIGENCE_API_KEY=<your-api-key>
AZURE_DOCUMENT_INTELLIGENCE_MODEL=prebuilt-document  # Optional, defaults to prebuilt-document
```

## Import Changes

Old imports:
```python
from konveyor.utils.azure import AzureDocumentService
from konveyor.config.azure import get_azure_credentials
```

New imports:
```python
from konveyor.services.documents import DocumentService
from konveyor.apps.documents.services import DjangoDocumentService
from konveyor.core.azure.mixins import ServiceLoggingMixin, AzureClientMixin
```

This restructuring improves code organization, maintainability, and separation of concerns while maintaining compatibility with existing code through the adapter pattern.

## 3. Implementation Details

### Service Implementations

1. **Document Service** (`services/documents/document_service.py`):
   ```python
   class DocumentService(ServiceLoggingMixin, AzureClientMixin):
       def __init__(self):
           self.endpoint = os.getenv('AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT')
           self.api_key = os.getenv('AZURE_DOCUMENT_INTELLIGENCE_API_KEY')
           self.model = os.getenv('AZURE_DOCUMENT_INTELLIGENCE_MODEL', 'prebuilt-document')
   ```

2. **RAG Service** (`services/rag/core/rag_service.py`):
   ```python
   class RAGService:
       def __init__(self):
           self.endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
           self.api_key = os.getenv('AZURE_OPENAI_API_KEY')
           self.embedding_deployment = os.getenv('AZURE_OPENAI_EMBEDDING_DEPLOYMENT')
   ```

### Framework Adapters

1. **Document Adapter** (`apps/documents/services/document_adapter.py`):
   ```python
   class DjangoDocumentService:
       def __init__(self):
           self._service = DocumentService()

       def __getattr__(self, name):
           return getattr(self._service, name)
   ```

2. **RAG Adapter** (`apps/rag/services/rag_adapter.py`):
   ```python
   class DjangoRAGService:
       def __init__(self):
           self._service = RAGService()
           self._search = SearchService()
   ```

### Azure Integration

1. **Common Utilities** (`core/azure/`):
   ```python
   # core/azure/mixins.py
   class ServiceLoggingMixin:
       def log_init(self, service_name: str) -> None:
           logger.info(f"Initializing {service_name}...")

   # core/azure/config.py
   def get_azure_credentials(service_name: str) -> Dict[str, str]:
       return {
           'endpoint': os.getenv(f'AZURE_{service_name}_ENDPOINT'),
           'api_key': os.getenv(f'AZURE_{service_name}_API_KEY')
       }
   ```

2. **Service Implementations** (`services/azure/`):
   ```python
   # services/azure/openai/client.py
   class AzureOpenAIClient:
       def __init__(self):
           self.endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
           self.api_key = os.getenv('AZURE_OPENAI_API_KEY')
           self.api_version = os.getenv('AZURE_OPENAI_API_VERSION', '2024-12-01-preview')
   ```

## 4. Migration Steps

1. **Service Consolidation**
   - [ ] Create new service directories
   - [ ] Move document and RAG services
   - [ ] Update import paths
   - [ ] Run test suite

2. **Azure Integration**
   - [ ] Organize Azure utilities
   - [ ] Move service implementations
   - [ ] Update configuration
   - [ ] Test Azure services

3. **Framework Integration**
   - [ ] Create framework adapters
   - [ ] Update Django views
   - [ ] Test integration
   - [ ] Document patterns

## 5. Historical Analysis

### Previous Document Service Analysis

### Current Locations
1. `apps/documents/services/document_service.py`
2. `services/documents/document_service.py`

### Implementation Analysis

#### Apps Version (`apps/documents/services/document_service.py`)
- More comprehensive implementation
- Includes Django models integration
- Has additional classes:
  - `DocumentParser`
  - `BatchProcessor`
- Uses Django-specific features:
  - Django models (Document, DocumentChunk)
  - Django settings and configurations
  - Django exceptions

#### Services Version (`services/documents/document_service.py`)
- Core functionality only
- Framework-agnostic implementation
- Focused on Azure Document Intelligence integration
- No Django dependencies

### Current Import References

1. Django App References:
```python
from konveyor.apps.documents.services.document_service import DocumentService
# Used in:
- apps/documents/views.py
- apps/search/tests/test_indexing_service.py
```

2. Services References:
```python
from konveyor.services.documents.document_service import DocumentService
# Used in:
- services/documents/tests/test_document_service.py
- apps/search/services/indexing_service.py
- apps/search/services/search_service.py
- apps/search/tests/test_search_service.py
```

### Recommendation

1. **Primary Location**: Move to `services/documents/document_service.py`
   - Core functionality should be framework-agnostic
   - Better separation of concerns
   - Follows the project's service-oriented architecture

2. **Required Changes**:
   - Create a Django-specific adapter in `apps/documents/services/`
   - Move Django-specific code to the adapter
   - Update imports in dependent files

### Implementation Plan

1. **Step 1**: Refactor Core Service
   - Keep core document processing in `services/documents/document_service.py`
   - Remove Django dependencies
   - Focus on Azure integration and file processing

2. **Step 2**: Create Django Adapter
   ```python
   # apps/documents/services/document_adapter.py
   from konveyor.services.documents.document_service import DocumentService

   class DjangoDocumentService:
       def __init__(self):
           self._service = DocumentService()

       def process_document(self, file_obj, filename):
           # Django-specific processing
           pass
   ```

3. **Step 3**: Update Import Statements
   - Update all Django app imports to use the adapter
   - Keep service layer imports pointing to core service

4. **Files to Update**:
   ```
   apps/documents/views.py
   apps/search/tests/test_indexing_service.py
   apps/search/services/indexing_service.py
   apps/search/services/search_service.py
   apps/search/tests/test_search_service.py
   services/documents/tests/test_document_service.py
   ```

### Next Steps

1. Create a backup of both files
2. Implement the core service refactoring
3. Create and test the Django adapter
4. Update import statements
5. Run the test suite to verify changes
