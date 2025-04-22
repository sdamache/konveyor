# Technical Context: Konveyor

## Technologies Used

- **Backend**: Python 3.10+, Django web framework, Django REST Framework
- **AI/LLM**: Azure OpenAI (embeddings, chat), Semantic Kernel (agent orchestration, skills, memory)
- **Azure SDKs**: azure-identity, azure-ai-formrecognizer, azure-search-documents, azure-storage-blob
- **Bot Integration**: Slack SDK, botbuilder-core, botbuilder-integration-aiohttp
- **Testing**: pytest, pytest-asyncio, pytest-aiohttp
- **Node.js Tooling**: Express, OpenAI, Anthropic SDK, CLI utilities (for development automation and PRD parsing)
- **Infrastructure**: Terraform for Azure resource provisioning (App Service, Cognitive Search, Blob Storage, PostgreSQL, Key Vault)

## Development Setup

- Python dependencies managed via requirements.txt and split environment files (base, development, production, testing)
- Node.js scripts for development automation (see package.json)
- Semantic Kernel skills and setup in `konveyor/skills/`
- Environment variables for Azure OpenAI and other secrets (optionally stored in Azure Key Vault)
- Local development uses SQLite; production uses PostgreSQL

## Technical Constraints

- Requires Azure account and provisioned services for production
- Azure OpenAI API keys and endpoints must be configured
- Persistent memory stores recommended for production agent memory
- All secrets should be managed via Azure Key Vault in production

## Tool Usage Patterns

- Semantic Kernel is initialized via `konveyor/skills/setup.py` and provides agentic orchestration for LLM-powered features
- Custom skills can be added under `konveyor/skills/` for new agent capabilities
- Bot integration supports Slack and Microsoft Bot Framework for chat-based access
- Document ingestion, search, and RAG workflows are modular and extensible

## Dependencies

- Python: Django, Azure SDKs, OpenAI, Semantic Kernel, Slack SDK, botbuilder, pytest
- Node.js: Express, OpenAI, Anthropic SDK, CLI utilities
- Azure: Cognitive Search, Blob Storage, Key Vault, PostgreSQL, App Service

## CI/CD and Testing

- GitHub Actions for continuous integration (lint, tests, build)
- Terraform for continuous deployment and environment management
- Unit, integration, and end-to-end tests for core services and RAG workflows

## Summary

Konveyor leverages a modern Python backend, Azure cloud services, and an agentic LLM framework (Semantic Kernel) to deliver a robust, extensible onboarding solution for software engineers. Node.js tooling supports development automation, and the system is designed for secure, cloud-native deployment with strong testing and CI/CD practices.
