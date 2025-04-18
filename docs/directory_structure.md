# Konveyor Project Directory Structure

## Core Directory Structure

```
 konveyor/
 ├── apps/              # Django applications (UI, API endpoints, Django-specific logic)
 │   ├── documents/     # Document management Django app
 │   │   ├── services/  # Django-specific services/adapters
 │   │   │   └── document_adapter.py  # Adapts core document service for Django
 │   │   ├── migrations/
 │   │   ├── tests/     # Tests for this Django app
 │   │   │   └── test_document_service.py # Tests the adapter
 │   │   ├── models.py  # Django models (e.g., Document metadata)
 │   │   └── views.py   # Django views/API endpoints
 │   ├── rag/           # RAG interface Django app
 │   │   ├── models.py
 │   │   ├── urls.py
 │   │   └── views.py
 │   └── search/        # Search functionality Django app
 │       ├── services/  # Django-specific services/adapters
 │       │   ├── indexing_service.py # Integrates with core indexing logic
 │       │   └── search_service.py   # Integrates with core search logic
 │       ├── management/
 │       │   └── commands/
 │       │       └── setup_search_index.py
 │       ├── migrations/
 │       ├── tests/     # Tests for this Django app
 │       ├── models.py
 │       └── views.py
 ├── core/              # Core, framework-agnostic functionality
 │   ├── azure_utils/   # Foundational Azure utilities
 │   │   ├── __init__.py
 │   │   ├── clients.py    # Azure SDK client factory/manager
 │   │   ├── config.py     # Central Azure configuration loading
 │   │   ├── mixins.py     # Common mixins (e.g., logging)
 │   │   ├── retry.py      # Retry decorator/logic
 │   │   └── service.py    # Base Azure service class
 │   ├── azure_adapters/ # Specific Azure service client implementations/wrappers
 │   │   ├── __init__.py
 │   │   └── openai/
 │   │       ├── __init__.py
 │   │       ├── client.py # Detailed OpenAI client logic
 │   │       └── tests/    # Tests for the OpenAI adapter
 │   │           └── test_integration.py
 │   │   └── tests/        # General tests for Azure adapters
 │   │       └── test_search_embedding.py
 │   ├── conversation/  # Conversation domain logic
 │   │   ├── __init__.py
 │   │   └── storage.py    # Conversation storage (CosmosDB/Redis)
 │   ├── documents/     # Document processing domain logic
 │   │   ├── __init__.py
 │   │   ├── document_service.py # Core document parsing/processing
 │   │   └── tests/        # Tests for core document service
 │   │       └── test_document_service.py
 │   ├── rag/           # RAG domain logic
 │   │   ├── __init__.py
 │   │   ├── context_service.py
 │   │   ├── rag_service.py
 │   │   └── templates.py  # RAG prompt templates
 │   └── __init__.py
 └── # (Other project root files: settings/, urls.py, etc.)
 ```

## Core/Azure Utils Module (`core/azure_utils/`) Details

The `core/azure_utils` module contains foundational, shared utilities for interacting with Azure services across the Konveyor project.

### Files Overview

1.  **`__init__.py`**: Standard Python package marker.
2.  **`clients.py`**: Defines `AzureClientManager`, a factory class responsible for creating configured Azure SDK client instances (e.g., `SearchClient`, `DocumentIntelligenceClient`, `BlobServiceClient`) based on loaded configuration. It centralizes client instantiation logic.
3.  **`config.py`**: Defines `AzureConfig`, a Singleton class that loads Azure service credentials, endpoints, and other settings from environment variables, providing a unified way to access configuration.
4.  **`mixins.py`**: Contains reusable Python mixin classes offering common Azure-related functionalities (e.g., standardized logging, base client access patterns) that can be incorporated into other classes.
5.  **`retry.py`**: Implements retry logic (e.g., using the `tenacity` library) via decorators like `@azure_retry` to handle transient Azure API errors gracefully.
6.  **`service.py`**: Defines a base class (`AzureService`) that other Azure-interacting services *can* inherit from, providing common initialization patterns involving `AzureConfig` and `AzureClientManager`, plus standardized logging methods.

## Core/Azure Adapters Module (`core/azure_adapters/`) Details

The `core/azure_adapters` module contains specific, detailed implementations or wrappers around individual Azure service clients. These adapters handle the direct interaction logic with Azure APIs.

### Submodules

1.  **`openai/`**:
    *   **`client.py`**: Contains the `AzureOpenAIClient` class, providing methods like `generate_embedding` and `generate_completion` that make direct calls to the Azure OpenAI REST APIs, including handling different API versions and request formatting.
    *   **`tests/`**: Contains integration tests specifically for the `AzureOpenAIClient`.
2.  **(Future Adapters):** This directory would house similar detailed client wrappers for other Azure services as needed (e.g., `storage/`, `search/`, `doc_intelligence/`).

## Apps/Documents Module Details

The `apps/documents` module handles document management and processing in the Konveyor project.

### Key Components

1. `services/document_adapter.py`
   - Adapts the core document service (`core.documents.document_service`) for use within the Django framework.
   - Handles Django-specific objects (e.g., `UploadedFile`).
   - May add Django-specific logic (e.g., saving results to Django models) before or after calling the core service.

2. `models.py`
   - Django models for document management (e.g., `Document` model storing metadata).
3. `views.py`
   - API endpoints (e.g., for document upload, status checks) using Django REST Framework or standard Django views.
4. `tests/`
   - Tests specifically for the Django `documents` app, focusing on the adapter, views, and models.

*(Removed redundant model/view descriptions)*

## Apps/Search Module Details

The `apps/search` module implements search functionality using Azure Cognitive Search.

### Key Components

1. `services/search_service.py`
   - Django-specific service that integrates with the core search logic (likely now in `core/search` or similar, TBD).
   - Provides methods used by Django views/commands.
   - Handles interaction with Django models if needed.

2. `services/indexing_service.py`
   - Django-specific service that integrates with core document processing (`core/documents`) and core search indexing logic.
   - Likely orchestrates the flow from a Django signal or view to parsing, chunking, embedding, and indexing via core components.

3. `management/commands/setup_search_index.py`
   - Django management command
   - Initializes and configures search indexes
   - Sets up vector search capabilities

4. `models.py`
   - Django models for search functionality
   - Models:
     - `SearchIndex`: Tracks indexed documents
     - `SearchResult`: Stores search results

5. `views.py`
   - API endpoints for search operations
   - Endpoints:
     - Search execution
     - Index management
     - Result retrieval

## Core/Documents Module (`core/documents/`) Details

The `core/documents` module contains the framework-agnostic logic for processing and managing documents.

### Key Components

1.  **`document_service.py`**: Implements the core `DocumentService` class responsible for parsing different file types (PDF, DOCX, MD, TXT) using appropriate libraries or Azure services (like Document Intelligence), extracting content, and potentially handling chunking logic (or delegating to a chunking service).
2.  **`tests/`**: Contains tests specifically for the core `DocumentService`, likely including integration tests that hit Azure Document Intelligence.

## Core/RAG Module (`core/rag/`) Details

The `core/rag` module implements the core Retrieval Augmented Generation functionality, independent of the Django framework.

### Key Components

1.  **`rag_service.py`**: Contains the main `RAGService` class orchestrating the RAG pipeline: processing queries, retrieving relevant context (likely interacting with search functionality), and generating completions using the context and an LLM.
2.  **`context_service.py`**: Manages context retrieval and formatting. Interacts with search services (potentially via `apps/search` or a core search component) to find relevant document chunks based on the query.
3.  **`templates.py`**: Defines prompt templates (`RAGPromptManager`, `PromptTemplate`) used for constructing requests to the LLM.

### Integration Points

*   Uses search functionality (potentially via `apps/search` services or a future `core/search` component) for context retrieval.
*   Uses the Azure OpenAI adapter (`core/azure_adapters/openai/client.py`) for generating embeddings and chat completions.
*   Uses core document services (`core/documents/`) for accessing processed document content/chunks.

## Core/Conversation Module (`core/conversation/`) Details

The `core/conversation` module handles the storage and retrieval of conversation history.

### Key Components

1.  **`storage.py`**: Defines `AzureStorageManager` responsible for interacting with Azure Cosmos DB (MongoDB API) for persistent storage and Azure Cache for Redis for caching recent messages. Provides methods like `create_conversation`, `add_message`, `get_conversation_messages`.

*(Note: The `utils/` directory was removed as its contents were consolidated or deemed unnecessary).*
