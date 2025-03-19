# Konveyor

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Built with Azure](https://img.shields.io/badge/Built%20with-Azure-0078D4.svg)](https://azure.microsoft.com)
[![Teams Integration](https://img.shields.io/badge/Teams-Integration-6264A7.svg)](https://developer.microsoft.com/en-us/microsoft-teams)

## Technical Overview

Konveyor is an AI-powered knowledge transfer system designed to address the critical engineering challenge of tribal knowledge silos within development teams. It leverages Azure AI services to create a context-aware reasoning system that integrates directly with existing developer workflows through Microsoft Teams, Slack, and VS Code.

The system implements a specialized Retrieval Augmented Generation (RAG) architecture optimized for engineering contexts, with advanced capabilities for code understanding, documentation navigation, and technical knowledge extraction.

## Problem Statement

Software engineering teams face significant challenges with knowledge transfer and onboarding:

1. **Tribal Knowledge Isolation**: Critical design decisions, architectural rationales, and implementation details often reside solely in the minds of senior engineers.

2. **Context Fragmentation**: Knowledge is scattered across documentation, code comments, pull requests, and communication channels, making it difficult to establish a coherent understanding.

3. **Workflow Disruption**: Traditional knowledge management solutions exist outside developer workflows, requiring context switching and reducing adoption.

4. **Code-Documentation Disconnect**: Documentation frequently becomes outdated or lacks the contextual understanding of why certain implementation decisions were made.

5. **Onboarding Inefficiency**: New engineers spend weeks or months reaching productivity, repeatedly interrupting senior engineers with the same questions.

## Technical Architecture

Konveyor implements a multi-component architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                      Client Interfaces                      │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐    │
│  │  Teams Bot    │  │   Slack Bot   │  │ VS Code Ext.  │    │
│  └───────┬───────┘  └───────┬───────┘  └───────┬───────┘    │
└─────────┼───────────────────┼───────────────────┼───────────┘
          │                   │                   │
          ▼                   ▼                   ▼
┌─────────────────────────────────────────────────────────────┐
│                       API Gateway                           │
└─────────┬───────────────────┬───────────────────┬───────────┘
          │                   │                   │
┌─────────▼───────┐ ┌─────────▼───────┐ ┌─────────▼───────────┐
│ Documentation   │ │ Code            │ │ Knowledge           │
│ Navigator       │ │ Understanding   │ │ Extraction          │
└─────────┬───────┘ └─────────┬───────┘ └─────────┬───────────┘
          │                   │                   │
┌─────────▼───────────────────▼───────────────────▼───────────┐
│                    Azure Cognitive Services                 │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐    │
│  │  Azure OpenAI │  │Azure Cognitive│  │ Azure Bot     │    │
│  │  Service      │  │Search         │  │ Service       │    │
│  └───────────────┘  └───────────────┘  └───────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Core Components

1. **Document Processing Pipeline**
   - Implements chunking strategies optimized for technical documentation
   - Utilizes Azure Form Recognizer for structured document parsing
   - Maintains document relationships and hierarchical structure

2. **Vector Storage Layer**
   - Leverages Azure Cognitive Search for vector storage and retrieval
   - Implements hybrid search combining semantic and keyword approaches
   - Maintains metadata for source attribution and context preservation

3. **RAG Implementation**
   - Utilizes Azure OpenAI Service for context-aware generation
   - Implements specialized prompt engineering for technical contexts
   - Maintains conversation state for multi-turn technical discussions

4. **Code Understanding Engine**
   - Performs Abstract Syntax Tree (AST) parsing for code structure analysis
   - Identifies inter-component relationships and dependencies
   - Generates contextual explanations of code snippets with architectural context

5. **Teams/Slack Integration**
   - Implements Bot Framework SDK for conversational interface
   - Utilizes adaptive cards for rich, interactive responses
   - Maintains conversation context across sessions

## Technical Differentiation

Konveyor differentiates from existing solutions through:

1. **Engineering-Specific RAG**: Optimized for technical documentation, code understanding, and architectural context rather than general knowledge management.

2. **Workflow Integration**: Delivers knowledge directly within developer tools (Teams, Slack, VS Code) rather than requiring context switching to separate applications.

3. **Code-Context Correlation**: Uniquely bridges the gap between code implementation and architectural decisions by understanding relationships between components.

4. **Azure AI Foundation**: Leverages enterprise-grade Azure AI services for security, compliance, and advanced capabilities specifically optimized for technical content.

5. **Tribal Knowledge Extraction**: Specialized in capturing and preserving the "why" behind technical decisions that is often lost in traditional documentation.

## Implementation Approach

Konveyor is built using a combination of:

- **Python FastAPI Backend**: For document processing, vector operations, and RAG implementation
- **Node.js Bot Framework**: For Teams and Slack integration
- **TypeScript VS Code Extension**: For IDE integration
- **Azure Cognitive Services**: For AI capabilities and vector storage
- **Docker Containerization**: For deployment flexibility

The system implements several advanced techniques:

- **Hierarchical Chunking**: Documents are processed using a hierarchical chunking strategy that preserves section relationships
- **Hybrid Retrieval**: Combines dense vector retrieval with sparse retrieval for improved accuracy
- **Context-Aware Prompting**: Dynamically constructs prompts based on query type, user role, and conversation history
- **AST-Based Code Analysis**: Parses code into abstract syntax trees for structural understanding
- **Bidirectional Traceability**: Maintains relationships between documentation and code implementations

## Getting Started

### Prerequisites

- Azure subscription with access to Azure OpenAI Service
- Node.js 18+ and Python 3.10+
- Microsoft Teams developer account or Slack developer account
- VS Code (for extension development)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-organization/konveyor.git
   cd konveyor
   ```

2. **Set up environment**
   ```bash
   # Backend setup
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   
   # Bot setup
   cd ../bot
   npm install
   ```

3. **Configure Azure resources**
   ```bash
   # Create required Azure resources
   az login
   ./scripts/setup_azure_resources.sh
   ```

4. **Start development servers**
   ```bash
   # Start backend
   cd backend
   uvicorn app.main:app --reload
   
   # Start bot in another terminal
   cd bot
   npm run dev
   ```

## Core Features

### Documentation Navigator

The Documentation Navigator component provides:

- Semantic search across documentation repositories
- Context-aware responses with source attribution
- Hierarchical navigation of complex documentation
- Multi-document correlation for comprehensive answers

### Code Understanding

The Code Understanding component offers:

- Contextual explanation of code snippets
- Identification of architectural patterns and design decisions
- Cross-reference between code and documentation
- Dependency and relationship analysis

### Onboarding Accelerator

The Onboarding Accelerator provides:

- Guided conversation flows for new team members
- Progressive knowledge discovery based on role and experience
- Automated identification of knowledge gaps
- Contextual recommendations for learning paths

## Contributing

We welcome contributions to Konveyor! Please see our [Contributing Guide](CONTRIBUTING.md) for details on how to get started.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

Konveyor builds upon several open-source projects and research:

- [RepoAgent](https://github.com/OpenBMB/RepoAgent) for code structure analysis patterns
- [AnythingLLM](https://github.com/Mintplex-Labs/anything-llm) for document processing approaches
- [LangChain](https://github.com/langchain-ai/langchain) for RAG implementation patterns
- [Microsoft Bot Framework](https://github.com/microsoft/botframework-sdk) for conversational interfaces

---

*Konveyor: Bridging the gap between tribal knowledge and engineering onboarding.*
