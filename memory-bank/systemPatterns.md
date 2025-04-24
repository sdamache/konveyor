# System Patterns: Konveyor

## System Architecture

Konveyor is architected as a modular, AI-driven onboarding and knowledge transfer platform for software engineers, built on Django and Azure. The system is designed for extensibility, security, and deep integration with cloud services.

### Key Architectural Patterns

- **Modular Django Backend**:
  - Apps for documents, search, RAG (Retrieve–Augment–Generate), and bot integration.
  - Each app encapsulates domain logic and exposes REST API endpoints.
  - Core services and adapters abstract Azure SDKs and business logic.

- **Semantic Kernel Framework**:
  - Modular skills architecture for AI capabilities in `konveyor/skills/` directory.
  - Integration with Azure OpenAI using credentials from Key Vault.
  - Volatile memory system for session-based data storage.
  - Agent orchestration layer for routing requests to appropriate skills.
  - PascalCase naming convention for Semantic Kernel skills.

- **RAG Workflow**:
  - Document ingestion: files are uploaded, parsed, chunked, and stored in Azure Blob Storage.
  - Indexing: document chunks are indexed in Azure Cognitive Search for semantic and hybrid search.
  - Query flow: user queries are routed through SearchService to retrieve top-k relevant chunks.
  - LLM response: retrieved context is combined with prompts and sent to Azure OpenAI for answer generation.
  - Bot integration: chat interfaces (Slack, Bot Framework) connect users to the RAG pipeline.

- **Infrastructure-as-Code**:
  - All Azure resources (App Service, Cognitive Search, Blob Storage, PostgreSQL, Key Vault) are provisioned via Terraform.
  - Environments for dev, test, and prod are managed as code.
  - GitHub Actions workflows for CI/CD with feature-branch naming conventions and PR review requirements.

- **Security Patterns**:
  - HTTPS enforced for all endpoints.
  - OAuth2/JWT for API authentication.
  - Secrets managed in Azure Key Vault.
  - Azure RBAC for resource access control.
  - Fallback mechanism for credentials when Key Vault is unavailable.

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
- **konveyor/skills**: Houses Semantic Kernel skills and framework setup:
  - **setup.py**: Initializes Semantic Kernel with Azure OpenAI integration and memory configuration.
  - **ChatSkill.py**: Implements basic chat functionality and utility functions.
  - **examples/**: Contains example implementations of Semantic Kernel skills.
  - Future skills will include DocumentationNavigator, CodeUnderstanding, and KnowledgeGapAnalyzer.
- **Konveyor-infra**: Infrastructure-as-Code for all Azure resources, supporting multi-environment deployment.

### Critical Implementation Paths

- Document upload → chunking → Blob Storage → Cognitive Search index
- User query → SearchService → retrieve chunks → RAGService → OpenAI → response
- Bot message → BotService → RAG pipeline → reply in chat
- Semantic Kernel workflow: User message → Bot Framework → Agent Orchestration → Semantic Kernel → Skill invocation → Azure OpenAI → formatted response
- Credential retrieval: Request → AzureConfig → Key Vault (primary) → Environment variables (fallback) → Semantic Kernel

### Design for Extensibility

- New document types and sources can be added via modular adapters.
- Additional chat platforms can be integrated by extending bot services.
- New AI capabilities can be added as Semantic Kernel skills in the konveyor/skills/ directory.
- Memory system can be extended from volatile to persistent storage as needed.
- Semantic Kernel skills can be composed and reused across different use cases.
- Future enhancements planned: real-time updates, multi-tenant onboarding, React SPA, analytics dashboards.

## Summary

Konveyor's architecture leverages modular Django apps, robust Azure integration, the RAG pattern, and Semantic Kernel framework to deliver a scalable, secure, and extensible onboarding solution for software engineers. The system combines traditional web application patterns with modern AI agent architecture through Semantic Kernel skills. It is designed for rapid iteration, cloud-native deployment, and deep integration with engineering workflows, while providing a flexible framework for adding new AI capabilities.
