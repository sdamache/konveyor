# Konveyor Architecture

## Overview

Konveyor follows a modular architecture with clear separation of concerns. The system is built with Django as the backend framework, with a focus on API-driven development to support multiple frontends.

## Components

### Backend (Django)

- **Core App**: Base functionality, utilities, and shared models
- **Users App**: User management, profiles, and authentication
- **API App**: REST API endpoints for integration with frontends and Azure services

### Azure Services

- **Azure OpenAI**: Provides AI capabilities for question answering and knowledge extraction
- **Azure Cognitive Search**: Indexes documents for efficient retrieval
- **Azure Blob Storage**: Stores static files and documents
- **Azure Database for PostgreSQL**: Persistent data storage
- **Azure Key Vault**: Secure storage of secrets and credentials
- **Azure Application Insights**: Monitoring and observability

## Data Flow

1. User submits a query or uploads a document
2. Django backend processes the request
3. For knowledge queries:
   - Query is sent to Azure OpenAI
   - Azure OpenAI processes the query using the organization's knowledge base
   - Results are returned to the user
4. For document uploads:
   - Document is stored in Azure Blob Storage
   - Document is indexed by Azure Cognitive Search
   - Azure OpenAI extracts key information from the document

## Security

- All communication is secured via HTTPS
- Authentication is handled via OAuth 2.0
- Sensitive configuration is stored in Azure Key Vault
- Access control is implemented at the API level


## Apps Structure

```text
konveyor/apps/
├── search/
│   ├── ...
├── documents/
│   ├── ...
```

### Search App: Key Classes & Functions

- **IndexingService** (indexing_service.py) ✅
  - Service for indexing documents and chunks in Azure Cognitive Search.
  - Methods:
    - `__init__`: Initializes with search and document services, batch size config.
    - `index_all_documents`: Bulk indexes all documents.
    - `index_document`: Indexes all chunks for a document.
    - `_index_chunk_batch`: Batch indexes chunks with retry logic.
    - `_calculate_batch_size`: Estimates optimal batch size for Azure limits.
- **SearchService** (search_service.py) ✅
  - Service for interacting with Azure Cognitive Search and OpenAI.
  - Methods:
    - `__init__`: Sets up Azure/OpenAI clients, creates index, tests embedding.
    - `create_search_index`: Creates search index with detailed config.
    - `get_index`: Fetches index config.
    - `delete_index`: Deletes index.
    - `generate_embedding`: Generates embeddings via Azure OpenAI.
    - `hybrid_search`: Combines vector and text search.
    - `vector_similarity_search`: Pure vector search.
    - `semantic_search`: Semantic hybrid search (may duplicate hybrid_search) ⚠️ (legacy/overlap)
    - `index_document_chunk`: Indexes a single chunk.
    - `get_chunk_content`: Loads chunk content via DocumentService.

### Documents App: Key Classes & Functions

- **DocumentService** (document_service.py) ⚠️/✅
  - Handles document storage, parsing, and chunking. (Some logic is legacy, see .bak)
  - Methods:
    - `__init__`: Initializes Azure config, blob client.
    - `process_document`: Stores and parses document, creates chunks. ⚠️ (legacy in .bak, refactor to use core)
    - `parse_file`: Parses file by MIME type (moved to DocumentParser in refactor).
    - `get_chunk_content`: Retrieves chunk from blob storage.
    - `_parse_pdf`, `_parse_docx`, `_parse_markdown`, `_parse_text`: File parsers (now in DocumentParser).
    - `store_document`, `store_chunk`: Store doc/chunk in blob/db.
- **DocumentParser** (document_service.py) ✅
  - Modern parser using Azure Document Intelligence.
  - Methods:
    - `parse_file`: Dispatches to correct parser.
    - `_parse_pdf`, `_parse_docx`, `_parse_markdown`, `_parse_text`: File parsing logic.
- **DjangoDocumentService** (document_adapter.py) ✅
  - Thin Django adapter over DocumentService for integration.
  - Methods:
    - `process_document`: Stores, splits, and chunks documents for Django models.
- **ChunkService** (chunk_service.py) ✅
  - Handles chunking logic for documents.
  - Methods:
    - `__init__`: Configures chunking parameters.

---

## RAG & Bot Apps Structure

```text
konveyor/apps/
├── rag/
│   ├── __init__.py
│   ├── models.py
│   ├── urls.py
│   ├── views.py
├── bot/
│   ├── app.py
│   ├── bot-template.json
│   ├── bot.py
│   ├── initialize_slack.py
│   ├── services/
│   │   ├── bot_settings_service.py
│   │   ├── secure_credential_service.py
│   │   ├── slack_channel_service.py
│   ├── setup_secure_storage.py
│   ├── slack_manifest.json
```

### RAG App: Key Classes & Functions

- **ConversationManager** (models.py) ✅
  - Manages conversations using Azure storage (CosmosDB/Redis).
  - Methods:
    - `__init__`: Sets up Azure storage manager.
    - `create_conversation`: Creates new conversation.
    - `add_message`: Adds message to conversation.
    - `get_conversation_messages`: Retrieves messages for a conversation.
- **ConversationViewSet** (views.py) ✅
  - Django ViewSet for conversation and RAG response APIs.
  - Methods:
    - `create`: Starts a new conversation.
    - `ask`: Handles user queries and generates responses.
    - `history`: Retrieves conversation history.
    - `list`: (Stub) List conversations for user.

### Bot App: Key Classes & Functions

- **KonveyorBot** (bot.py) ✅
  - Main bot logic for handling messages and member events.
  - Methods:
    - `on_message_activity`: Handles incoming user messages.
    - `on_members_added_activity`: Handles new member joins.
- **BotSettingsService** (services/bot_settings_service.py) ✅
  - Provides bot configuration and channel settings.
  - Methods:
    - `get_settings`: Returns bot settings dataclass.
    - `get_channel_config`: Returns Azure Bot Service channel config.
- **SecureCredentialService** (services/secure_credential_service.py) ✅
  - Manages bot credentials using Azure Key Vault.
  - Methods:
    - `store_bot_credentials`: Stores credentials in Key Vault.
    - `get_bot_credentials`: Retrieves credentials from Key Vault.
    - `_set_secret`, `_get_secret`: Internal helpers for secret management.
- **SlackChannelService** (services/slack_channel_service.py) ✅
  - Configures and verifies Slack channel integration with Azure Bot Service.
  - Methods:
    - `configure_channel`: Sets up Slack channel in Azure.
    - `verify_channel`: Checks Slack channel status.

**Legend:**
- ✅ = Modern/clean code, uses new core or best practices
- ⚠️ = Legacy/redundant/overlapping logic (should be refactored or already migrated)

## Core Directory Structure & Key Functions

Below is the current structure of the `konveyor/core/` directory, along with high-level classes/functions and their roles. For full details and rationale, see [Refactoring Plan](./refactoring_plan.md).

```text
konveyor/core/
├── __init__.py
├── azure/
│   └── service.py
│       └── AzureService
│           - Base class for Azure services with logging and client management.
│           - Methods:
│           • __init__: Initializes service with name and Azure clients.
│           • log_init/log_success/log_error/log_warning/log_debug: Logging utilities.
│           • log_azure_credentials: Logs endpoint/key safely.
│           • _validate_config: Validates required config for the service.
├── azure_adapters/
│   ├── openai/
│   │   ├── client.py
│   │   │   └── AzureOpenAIClient
│   │   │       - Client for interacting with Azure OpenAI API.
│   │   │       - Methods:
│   │   │           • __init__: Initializes the client with API key, endpoint, versions, and deployment names.
│   │   │           • generate_embedding: Generates an embedding for given text, with retry logic and error handling.
│   │   │           • generate_completion: Generates a chat completion response for a list of messages.
│   │   └── tests/
│   └── tests/
│       └── test_search_embedding.py
├── azure_utils/
│   ├── __init__.py
│   ├── clients.py
│   │   └── AzureClientManager
│   │       - Manages Azure client initialization and configuration.
│   │       - Provides methods to initialize clients for various Azure services, using retry logic.
│   ├── config.py
│   │   └── AzureConfig
│   │       - Unified Azure configuration management (Singleton).
│   │       - Handles environment variable loading, service-specific config, and key retrieval.
│   ├── mixins.py
│   │   └── AzureClientMixin
│   │       - Mixin providing Azure client initialization methods.
│   │       - Methods to initialize OpenAI, Search, and Document Intelligence clients.
│   │   └── AzureServiceConfig
│   │       - Configuration manager for Azure services.
│   │       - Loads and validates endpoint/key for a given Azure service.
│   │   └── ServiceLoggingMixin
│   │       - Mixin providing standardized logging methods for services.
│   │       - Methods for logging init, credentials, success, and errors.
│   ├── retry.py
│   │   └── azure_retry
│   │       - Decorator for retrying Azure operations with exponential backoff.
│   │       - Used to wrap Azure SDK calls for resilience.
│   └── service.py
│       └── AzureService
│           - Base class for Azure services with logging and client management.
│           - Standardizes config, logging, and client management for all Azure services.
├── conversation/
│   └── storage.py
│       └── AzureStorageManager
│           - Manages interactions with Azure storage (Cosmos DB/MongoDB and Redis).
│           - Methods:
│           • __init__: Sets up MongoDB/Cosmos and Redis clients, collections, and indexes.
│           • create_conversation: Creates a new conversation (async).
│           • add_message: Adds message to conversation, stores in DB and Redis (async).
│           • get_conversation_messages: Retrieves messages from Redis or DB (async).
│           • delete_conversation: Deletes conversation/messages from DB and cache (async).
│           • initialize/_ensure_database_exists: Ensures DB/collections/indexes exist (async).
│           • __aenter__/__aexit__: Async context manager for resource cleanup.
│           • _convert_mongodb_to_cosmos_connection_string: Converts connection strings.
│       └── MongoJSONEncoder
│           - JSON encoder for MongoDB ObjectId serialization.
│           - Method:
│           • default: Converts ObjectId to string for JSON.
├── documents/
│   ├── __init__.py
│   ├── document_service.py
│   │   └── DocumentService
│   │       - Service for handling document operations using Azure Document Intelligence.
│   │       - Methods:
│   │           • __init__: Initializes with Azure Document Intelligence client.
│   │           • parse_file: Parses PDF, DOCX, Markdown, or text using Azure.
│   │           • _parse_pdf/_parse_docx/_parse_markdown/_parse_text: File-type specific parsing with error handling and metadata extraction.
│   │           • store_chunk_content/get_chunk_content: Store/retrieve doc chunks in Azure Blob Storage.
│   │           • initialize_document_intelligence_client: Sets up Azure client.
│   │           • log_init/log_success/log_error/log_warning: Logging utilities.
│   ├── document_service.py.bak
│   └── tests/
│       ├── __init__.py
│       ├── test_document_service.py
│       └── test_files/
├── rag/
│   └── templates.py
│       └── RAGPromptManager
│           - Manages prompt templates for different RAG scenarios.
│           - Methods:
│           • __init__: Initializes default templates (knowledge, code).
│           • get_template: Retrieves a prompt template by type.
│           • add_template: Adds a new prompt template.
│           • format_prompt: Formats a template with parameters.
│       └── PromptTemplate
│           - Base class for RAG prompt templates.
│           - Fields: system_message, user_message.
│           - Method:
│           • format: Formats the template with given parameters.
```


### Example Key Functions (abbreviated)

- **AzureConfig.get_endpoint(service)**: Returns endpoint for given Azure service
- **AzureClientManager.get_openai_client()**: Returns configured Azure OpenAI client
- **AzureClientMixin.initialize_openai_client()**: Initializes OpenAI clients
- **AzureOpenAIClient.generate_embedding(text)**: Returns embedding vector for input
- **AzureOpenAIClient.generate_completion(messages)**: Returns chat completion for messages

For a full, up-to-date architectural map (including class/function docstrings), see the [Refactoring Plan](./refactoring_plan.md#phase-6-application-code-cleanup--documentation-finalization).

## Future Enhancements

- Real-time notifications via WebSockets
- Integration with Microsoft Teams
- Mobile application support
