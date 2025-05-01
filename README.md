# Konveyor: AI-Powered Knowledge Transfer Agent

Konveyor is an AI-powered knowledge transfer agent designed to accelerate software engineer onboarding and facilitate knowledge sharing within organizations. It leverages Microsoft's Semantic Kernel framework and Azure services to provide intelligent, context-aware assistance through Slack.

## Problem Statement

Software engineer onboarding is a costly, inefficient process plagued by:
- Scattered documentation and knowledge silos
- Limited access to mentorship from senior engineers
- Difficulty understanding complex, undocumented codebases
- Overwhelming or unstructured onboarding experiences

Organizations routinely lose over $30,000 per new engineer in lost productivity, mentor time, and delayed project contributions. Konveyor directly addresses these challenges with a specialized AI agent that understands organizational context.

## Key Features

### Documentation Navigator
- Searches and retrieves relevant documentation with context awareness
- Preprocesses queries to understand onboarding-related questions
- Formats responses with proper source citations
- Maintains conversation context for natural follow-up questions

### Code Understanding
- Parses and explains code snippets with language detection
- Analyzes code structure and organizational patterns
- Generates clear explanations with syntax highlighting
- Connects code explanations to architectural context

### Knowledge Gap Analyzer
- Maps questions to a taxonomy of knowledge areas
- Tracks user confidence across different domains
- Identifies potential knowledge gaps
- Suggests relevant resources for learning

### Slack Integration
- Seamless interaction through familiar chat interface
- Thread support for organized conversations
- Rich message formatting for code and technical content
- Slash commands for specialized functionality

## Architecture

Konveyor is built on a modern, modular architecture:

- **Microsoft Semantic Kernel** for AI orchestration and skill management
- **Azure OpenAI** for advanced language understanding and generation
- **Azure Cognitive Search** for semantic document retrieval
- **Azure Key Vault** for secure credential management
- **Slack Bot Framework** for user interaction

The system follows an agent-based architecture with specialized skills that can be invoked based on user needs. A memory system maintains conversation context and tracks user knowledge.

## Getting Started

### Prerequisites

- Python 3.10+
- Azure account with appropriate services
- Slack workspace with admin privileges

### Installation

1. Clone the repository
   ```bash
   git clone https://github.com/yourusername/konveyor.git
   cd konveyor
   ```

2. Create a virtual environment
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies
   ```bash
   pip install -r requirements/development.txt
   ```

4. Set up environment variables
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. Run migrations
   ```bash
   python manage.py migrate
   ```

6. Start the development server
   ```bash
   python manage.py runserver
   ```

## Configuration

Konveyor requires the following environment variables:

- `AZURE_OPENAI_ENDPOINT`: Azure OpenAI endpoint URL
- `AZURE_OPENAI_API_KEY`: API key for Azure OpenAI
- `AZURE_OPENAI_CHAT_DEPLOYMENT`: Deployment name (default: `gpt-4-turbo`)
- `AZURE_OPENAI_EMBEDDING_DEPLOYMENT`: Embedding model deployment
- `AZURE_COGNITIVE_SEARCH_ENDPOINT`: Azure Cognitive Search endpoint
- `AZURE_COGNITIVE_SEARCH_API_KEY`: API key for Azure Cognitive Search
- `AZURE_COGNITIVE_SEARCH_INDEX_NAME`: Index name for document search
- `SLACK_BOT_TOKEN`: Bot token for Slack integration
- `SLACK_SIGNING_SECRET`: Signing secret for Slack integration

## Deployment

Konveyor is designed to be deployed on Azure App Service:

1. Provision required Azure resources using Terraform
2. Configure environment variables in Azure App Service
3. Deploy the application using GitHub Actions CI/CD pipeline

## Documentation

For more detailed information, see the following documentation:

- [Architecture Overview](docs/architecture.md)
- [User Guide](docs/user_guide.md)
- [Semantic Kernel Setup](docs/semantic_kernel_setup.md)
- [Slack Integration](docs/slack_slash_commands.md)

## Future Enhancements

- Persistent memory system using Azure Cognitive Search
- Multi-tenant onboarding capabilities
- Additional skills for specialized knowledge domains
- Integration with Microsoft Teams
- Analytics dashboard for knowledge gap visualization
- Automated knowledge base updates