# Konveyor Project Directory Structure

## Core Directory Structure

```
konveyor/
├── apps/              # Django applications
│   ├── documents/     # Document management Django app
│   │   ├── services/
│   │   │   └── document_adapter.py  # Django adapter for document service
│   │   ├── migrations/
│   │   ├── tests/
│   │   │   ├── conftest.py
│   │   │   └── test_document_service.py
│   │   ├── models.py
│   │   └── views.py
│   ├── rag/          # RAG interface Django app
│   │   ├── models.py
│   │   ├── urls.py
│   │   └── views.py
│   └── search/       # Search functionality Django app
│       ├── services/
│       │   ├── indexing_service.py
│       │   └── search_service.py
│       ├── management/
│       │   └── commands/
│       │       └── setup_search_index.py
│       ├── migrations/
│       ├── tests/
│       ├── models.py
│       └── views.py
├── core/             # Core functionality
│   └── azure/        # Common Azure utilities
│       ├── mixins.py    # Shared service mixins (logging, client init)
│       └── config.py    # Basic configuration utilities
├── services/         # Core services
│   └── documents/    # Document processing service
│       ├── document_service.py
│       └── tests/
│           ├── test_files/
│           └── test_document_service.py
│   └── azure/        # Azure service implementations
│       ├── clients.py     # Azure client implementations
│       ├── config.py      # Service-specific configurations
│       ├── mixins.py      # Service-specific mixins
│       ├── openai_client.py  # OpenAI integration
│       ├── rag_templates.py  # RAG prompt templates
│       ├── retry.py       # Azure retry policies
│       ├── service.py     # Azure service classes
│       └── storage.py     # Azure storage operations
├── services/         # Core business logic
│   ├── documents/    # Document processing service
│   │   ├── document_service.py
│   │   └── tests/
│   │       └── test_document_service.py
│   └── rag/         # RAG implementation
│       ├── context_service.py
│       └── rag_service.py
└── utils/           # Utility functions
```

## Core/Azure Module Details

The `core/azure` module contains essential Azure service integrations and utilities used throughout the Konveyor project.

### Files Overview

1. `__init__.py`
   - Module initialization file
   - Exports key classes and functions for Azure integration

2. `clients.py`
   - Core client management for Azure services
   - Key Classes:
     - `AzureClientManager`: Central manager for Azure service clients
       - `get_search_clients()`: Returns SearchIndexClient and SearchClient
       - `get_openai_client()`: Returns configured AzureOpenAI client
       - `get_document_intelligence_client()`: Returns DocumentIntelligenceClient
       - `get_blob_service_client()`: Returns BlobServiceClient
       - `get_keyvault_client()`: Returns SecretClient
   - Implements retry logic and error handling for all client operations

3. `config.py`
   - Azure service configuration management
   - Key Classes:
     - `AzureConfig`: Configuration settings for Azure services
       - Manages endpoint URLs, API keys, and deployment names
       - Handles environment variable loading for:
         - AZURE_OPENAI_ENDPOINT
         - AZURE_OPENAI_API_KEY
         - AZURE_OPENAI_CHAT_DEPLOYMENT
         - AZURE_OPENAI_EMBEDDING_DEPLOYMENT
         - AZURE_SEARCH_ENDPOINT
         - AZURE_SEARCH_KEY
         - Other Azure service configurations

4. `mixins.py`
   - Reusable mixins for Azure service integration
   - Classes:
     - `AzureClientMixin`: Base mixin for Azure client access
     - `SearchClientMixin`: Mixin for search operations
     - `OpenAIClientMixin`: Mixin for OpenAI operations

5. `openai_client.py`
   - Azure OpenAI service integration
   - Key Functions:
     - `generate_embeddings()`: Creates embeddings using Azure OpenAI
     - `generate_chat_completion()`: Handles chat completions
     - `create_openai_client()`: Configures OpenAI client with proper settings

6. `rag_templates.py`
   - Templates and prompts for RAG implementation
   - Contains:
     - System prompts for chat completions
     - Context injection templates
     - Response formatting templates

7. `retry.py`
   - Retry logic for Azure service calls
   - Features:
     - `azure_retry` decorator for automatic retries
     - Exponential backoff implementation
     - Error categorization and handling
     - Configurable retry counts and delays

8. `service.py`
   - Base service classes for Azure integration
   - Classes:
     - `BaseAzureService`: Abstract base class for Azure services
     - `AzureServiceMixin`: Common service functionality

9. `storage.py`
   - Azure storage service integration
   - Key Functions:
     - Blob container management
     - File upload/download operations
     - Storage access configuration

## Apps/Documents Module Details

The `apps/documents` module handles document management and processing in the Konveyor project.

### Key Components

1. `services/document_service.py`
   - Primary document processing service
   - Key Functions:
     - `process_document()`: Main document processing pipeline
     - `parse_file()`: File parsing with Azure Document Intelligence
     - `extract_text()`: Text extraction from parsed documents

2. `services/chunk_service.py`
   - Document chunking and segmentation
   - Key Functions:
     - `chunk_document()`: Splits documents into processable chunks
     - `optimize_chunks()`: Optimizes chunk size for embedding

3. `models.py`
   - Django models for document management
   - Models:
     - `Document`: Stores document metadata and processing status
     - `DocumentChunk`: Represents segmented document chunks

4. `views.py`
   - API endpoints for document operations
   - Endpoints:
     - Document upload
     - Processing status
     - Document retrieval

## Apps/Search Module Details

The `apps/search` module implements search functionality using Azure Cognitive Search.

### Key Components

1. `services/search_service.py`
   - Core search functionality
   - Key Functions:
     - `search()`: Performs vector and keyword search
     - `hybrid_search()`: Combines vector and keyword search results
     - `get_document_by_id()`: Retrieves specific documents

2. `services/indexing_service.py`
   - Manages search index operations
   - Key Functions:
     - `create_index()`: Sets up search index schema
     - `index_document()`: Indexes document chunks
     - `update_index()`: Updates existing index entries

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

## Config/Azure Module Details

The configuration module for Azure services, split across two locations:

### 1. `config/azure.py`
   - Main Azure configuration file
   - Key Components:
     - Package dependency checks and imports
     - `AzureConfig` class:
       - Credential management
       - Client initialization methods
       - Environment variable handling
     - Service client factory methods:
       - `get_document_intelligence_client()`
       - `get_openai_client()`
       - `get_search_client()`
       - `get_storage_client()`

### 2. `config/azure/` Directory
   1. `config.py`
      - Detailed Azure service configurations
      - Environment variable management
      - Service-specific settings

   2. `service.py`
      - Base service configurations
      - Common service utilities
      - Authentication helpers

## Services/RAG Module Details

The `services/rag` module implements the Retrieval Augmented Generation functionality.

### Key Components

1. `rag_service.py`
   - Core RAG implementation
   - Key Functions:
     - `generate_response()`: Main RAG pipeline
     - `process_query()`: Query processing
     - `retrieve_context()`: Context retrieval from vector store
     - `generate_completion()`: Response generation with context

2. `context_service.py`
   - Context management for RAG
   - Key Functions:
     - `get_relevant_context()`: Retrieves relevant document chunks
     - `format_context()`: Formats context for prompt injection
     - `rank_contexts()`: Ranks context by relevance

### Integration Points

- Uses `apps/search` for vector search
- Uses `core/azure/openai_client.py` for embeddings and completions
- Uses `apps/documents` for document processing

## Services Module Details

The `services` module contains core business logic implementations separate from Django apps.

### Directory Structure

```
services/
├── documents/           # Document processing core service
│   ├── __init__.py
│   ├── document_service.py
│   └── tests/
│       └── test_document_service.py
└── rag/                # RAG implementation service
    ├── __init__.py
    ├── context_service.py
    └── rag_service.py
```

### 1. Documents Service (`services/documents/`)

Core document processing implementation, independent of Django.

#### Key Components:

1. `document_service.py`
   - Document processing using Azure Document Intelligence
   - Key Functions:
     - `parse_file()`: Main document parsing pipeline
     - `_parse_pdf()`: PDF parsing with Azure Document Intelligence
     - `_parse_docx()`: DOCX parsing
     - `_parse_markdown()`: Markdown parsing
     - `_parse_text()`: Plain text parsing
   - Features:
     - Error handling and logging
     - Azure client management
     - Multiple format support

2. `tests/test_document_service.py`
   - Unit tests for document processing
   - Test cases for different file formats
   - Azure integration testing

### 2. RAG Service (`services/rag/`)

Retrieval Augmented Generation implementation.

#### Key Components:

1. `rag_service.py`
   - Core RAG implementation
   - Key Functions:
     - `generate_response()`: Main RAG pipeline
     - `process_query()`: Query preprocessing
     - `retrieve_context()`: Context retrieval
     - `generate_completion()`: Response generation
   - Features:
     - Integration with Azure OpenAI
     - Context management
     - Response formatting

2. `context_service.py`
   - Context handling for RAG
   - Key Functions:
     - `get_relevant_context()`: Context retrieval
     - `format_context()`: Context formatting
     - `rank_contexts()`: Context ranking
   - Features:
     - Vector similarity search
     - Context optimization
     - Relevance scoring

### Integration Flow

1. Document Processing Flow:
   ```
   Document -> DocumentService -> Chunks -> Search Index
   ```

2. RAG Query Flow:
   ```
   Query -> RAGService -> ContextService -> Search -> OpenAI -> Response
   ```
