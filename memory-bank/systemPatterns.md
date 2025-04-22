# System Patterns: Konveyor

## System Architecture

Konveyor is architected as a modular, AI-driven onboarding and knowledge transfer platform for software engineers, built on Django and Azure. The system is designed for extensibility, security, and deep integration with cloud services.

### Key Architectural Patterns

- **Modular Django Backend**: 
  - Apps for documents, search, RAG (Retrieve–Augment–Generate), and bot integration.
  - Each app encapsulates domain logic and exposes REST API endpoints.
  - Core services and adapters abstract Azure SDKs and business logic.

- **RAG Workflow**:
  - Document ingestion: files are uploaded, parsed, chunked, and stored in Azure Blob Storage.
  - Indexing: document chunks are indexed in Azure Cognitive Search for semantic and hybrid search.
  - Query flow: user queries are routed through SearchService to retrieve top-k relevant chunks.
  - LLM response: retrieved context is combined with prompts and sent to Azure OpenAI for answer generation.
  - Bot integration: chat interfaces (Slack, Bot Framework) connect users to the RAG pipeline.

- **Infrastructure-as-Code**:
  - All Azure resources (App Service, Cognitive Search, Blob Storage, PostgreSQL, Key Vault) are provisioned via Terraform.
  - Environments for dev, test, and prod are managed as code.

- **Security Patterns**:
  - HTTPS enforced for all endpoints.
  - OAuth2/JWT for API authentication.
  - Secrets managed in Azure Key Vault.
  - Azure RBAC for resource access control.

- **Testing Strategy**:
  - Unit tests for core logic and services.
  - Integration tests for service and API layers.
  - End-to-end tests for RAG workflows and bot interactions.

### Component Relationships

- **konveyor/apps/documents**: Handles document ingestion, parsing, chunking, and storage. Delegates to core DocumentService.
- **konveyor/apps/search**: Manages semantic and hybrid search, batch indexing, and search endpoints. Wraps core SearchService.
- **konveyor/apps/rag**: Orchestrates RAG workflows, conversation management, and context retrieval. Uses core RAGService.
- **konveyor/apps/bot**: Integrates with Slack and Bot Framework for chat-based access. Implements bot logic and secure credential storage.
- **konveyor/core**: Contains shared utilities, Azure adapters, and core business logic for document, search, and RAG services.
- **Konveyor-infra**: Infrastructure-as-Code for all Azure resources, supporting multi-environment deployment.

### Critical Implementation Paths

- Document upload → chunking → Blob Storage → Cognitive Search index
- User query → SearchService → retrieve chunks → RAGService → OpenAI → response
- Bot message → BotService → RAG pipeline → reply in chat

### Design for Extensibility

- New document types and sources can be added via modular adapters.
- Additional chat platforms can be integrated by extending bot services.
- Future enhancements planned: real-time updates, multi-tenant onboarding, React SPA, analytics dashboards.

## Summary

Konveyor's architecture leverages modular Django apps, robust Azure integration, and the RAG pattern to deliver a scalable, secure, and extensible onboarding solution for software engineers. The system is designed for rapid iteration, cloud-native deployment, and deep integration with engineering workflows.
