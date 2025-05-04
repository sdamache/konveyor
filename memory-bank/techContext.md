# Technical Context: Konveyor

## Technologies Used

- **Backend**: Python 3.10+, Django web framework, Django REST Framework
- **AI/LLM**:
  - Azure OpenAI (embeddings, chat)
  - Semantic Kernel 1.0.1 (agent orchestration, skills, memory)
  - AzureChatCompletion and AzureTextEmbedding services
  - VolatileMemoryStore for session-based data storage
- **Azure SDKs**:
  - azure-identity for authentication
  - azure-ai-formrecognizer for document processing
  - azure-search-documents for cognitive search
  - azure-storage-blob for blob storage
  - azure-keyvault-secrets for secure credential management
- **Bot Integration**:
  - Slack SDK for Slack integration
  - botbuilder-core and botbuilder-integration-aiohttp for Bot Framework
  - BotFrameworkAdapter for message handling
- **Testing**: pytest, pytest-asyncio, pytest-aiohttp
- **Node.js Tooling**: Express, OpenAI, Anthropic SDK, CLI utilities (for development automation and PRD parsing)
- **Infrastructure**:
  - Terraform for Azure resource provisioning (App Service, Cognitive Search, Blob Storage, PostgreSQL, Key Vault)
  - GitHub Actions for CI/CD with branch naming and commit message validation

## Development Setup

- Python dependencies managed via requirements.txt and split environment files (base, development, production, testing)
- Node.js scripts for development automation (see package.json)
- Semantic Kernel skills and setup in `konveyor/skills/`:
  - `setup.py` for Kernel initialization and Azure OpenAI integration
  - `ChatSkill.py` for basic chat functionality and utility functions
  - Example skills in `examples/` directory
  - PascalCase naming convention for Semantic Kernel skills
- Environment variables for Azure OpenAI and other secrets (optionally stored in Azure Key Vault)
- Fallback mechanism for credentials when Key Vault is unavailable
- Local development uses SQLite; production uses PostgreSQL
- Task-master for task management and tracking implementation progress

## Technical Constraints

- Requires Azure account and provisioned services for production
- Azure OpenAI API keys and endpoints must be configured
- Semantic Kernel 1.0.1 compatibility must be maintained
- Volatile memory is used for development, but persistent memory stores are recommended for production
- All secrets should be managed via Azure Key Vault in production
- Redundancy between ChatSkill and existing RAG implementation needs to be addressed
- PEP 8 naming conventions for Python code and PascalCase for Semantic Kernel Skills

## Tool Usage Patterns

- Semantic Kernel is initialized via `konveyor/skills/setup.py` and provides orchestration for LLM-powered features:
  - `create_kernel()` function configures Semantic Kernel with Azure OpenAI services
  - Key Vault integration with fallback to environment variables for credentials
  - Volatile memory store for session-based data storage
- Custom skills can be added under `konveyor/skills/` for new agent capabilities:
  - Skills use `@kernel_function` decorator to expose functions to Semantic Kernel
  - ChatSkill demonstrates basic chat functionality and utility functions
- Bot Framework integration in `konveyor/apps/bot/`:
  - BotFrameworkAdapter for message handling
  - KonveyorBot class for processing messages and member additions
- Document ingestion, search, and RAG workflows are modular and extensible

## Dependencies

- Python:
  - Django and Django REST Framework for web application framework
  - Azure SDKs for cloud service integration
  - Semantic Kernel 1.0.1 for agent orchestration and skills
  - Azure OpenAI for LLM capabilities
  - Bot Framework (botbuilder-core, botbuilder-integration-aiohttp) for chat integration
  - Slack SDK for Slack integration
  - pytest, pytest-asyncio, pytest-aiohttp for testing
- Node.js:
  - Express for web server
  - OpenAI and Anthropic SDKs for AI capabilities
  - task-master for task management and tracking
  - CLI utilities for development automation
- Azure:
  - Cognitive Search for document indexing and search
  - Blob Storage for document storage
  - Key Vault for secret management
  - PostgreSQL for production database
  - App Service for application hosting

## CI/CD and Testing

- GitHub Actions for continuous integration:
  - Linting and code quality checks
  - Unit and integration tests
  - Docker image building
  - Feature-branch naming conventions enforcement (feat/task-<id>-<desc>)
  - PR review requirements
  - Conventional Commits formatting validation
- Terraform for continuous deployment and environment management:
  - Infrastructure-as-Code for all Azure resources
  - Environment-specific configurations (dev, test, prod)
  - Secure credential management
- Testing strategy:
  - Unit tests for core services and Semantic Kernel skills
  - Integration tests for service and API layers
  - End-to-end tests for RAG workflows and bot interactions
  - Test scaffolding exists but needs expansion

## Summary

Konveyor leverages a modern Python backend, Azure cloud services, and the Semantic Kernel framework to deliver a robust, extensible onboarding solution for software engineers. The system combines Django's web application capabilities with Semantic Kernel's AI orchestration to create a powerful knowledge transfer platform.

Key technical highlights include:
- Semantic Kernel 1.0.1 integration with Azure OpenAI
- Modular skill architecture for AI capabilities
- Secure credential management with Key Vault and fallback mechanisms
- Bot Framework integration for chat interfaces
- Infrastructure-as-Code with Terraform and GitHub Actions for CI/CD
- Comprehensive testing strategy across all layers

The system is designed for secure, cloud-native deployment with strong testing and CI/CD practices, while providing a flexible framework for adding new AI capabilities through Semantic Kernel skills.
