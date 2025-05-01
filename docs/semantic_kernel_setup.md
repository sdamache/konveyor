# Semantic Kernel Setup and Usage

## 1. Directory Structure

The Semantic Kernel implementation in Konveyor is organized as follows:

- `konveyor/core/generation/`: Core Semantic Kernel setup
  - `kernel.py`: Kernel initialization and configuration
  - `memory.py`: Memory system configuration

- `konveyor/core/chat/`: Agent orchestration
  - `orchestration.py`: Agent orchestration layer
  - `router.py`: Request routing to appropriate skills

- `konveyor/core/kernel/`: Kernel configuration
  - `config.py`: Configuration settings for Semantic Kernel

- `konveyor/skills/`: Specialized skill implementations
  - `documentation_navigator/`: Documentation search and retrieval
  - `code_understanding/`: Code parsing and explanation
  - `knowledge_analyzer/`: Knowledge gap analysis
  - `common/`: Shared utilities and base classes

## 2. Installation

Install Semantic Kernel SDK and required dependencies:

```bash
pip install semantic-kernel==0.4.0.dev0
pip install azure-identity azure-keyvault-secrets
pip install numpy pandas matplotlib
```

## 3. Configuration

Set required environment variables (stored in Azure Key Vault for production):

- `AZURE_OPENAI_ENDPOINT`: Azure OpenAI endpoint URL
- `AZURE_OPENAI_API_KEY`: API key for Azure OpenAI
- `AZURE_OPENAI_CHAT_DEPLOYMENT`: Deployment name (default: `gpt-4-turbo`)
- `AZURE_OPENAI_EMBEDDING_DEPLOYMENT`: Embedding model deployment (default: `text-embedding-ada-002`)
- `AZURE_OPENAI_API_VERSION`: API version (default: `2024-02-15-preview`)
- `AZURE_COGNITIVE_SEARCH_ENDPOINT`: Azure Cognitive Search endpoint
- `AZURE_COGNITIVE_SEARCH_API_KEY`: API key for Azure Cognitive Search
- `AZURE_COGNITIVE_SEARCH_INDEX_NAME`: Index name for document search

## 4. Kernel Initialization

```python
from konveyor.core.generation.kernel import initialize_kernel
from konveyor.core.generation.memory import initialize_memory

# Initialize the kernel with Azure OpenAI
kernel = initialize_kernel()

# Initialize the memory system
memory = initialize_memory(kernel)

# Register skills
from konveyor.skills.documentation_navigator.skill import DocumentationNavigatorSkill
from konveyor.skills.code_understanding.skill import CodeUnderstandingSkill
from konveyor.skills.knowledge_analyzer.skill import KnowledgeGapAnalyzerSkill

# Initialize services
from konveyor.core.azure_utils.clients import AzureClientManager
azure_clients = AzureClientManager()
search_service = azure_clients.get_search_service()

# Register skills with the kernel
doc_navigator = DocumentationNavigatorSkill(kernel, search_service)
code_understanding = CodeUnderstandingSkill(kernel)
knowledge_analyzer = KnowledgeGapAnalyzerSkill(kernel)
```

## 5. Memory System

Konveyor uses Semantic Kernel's memory capabilities for conversation context and knowledge tracking:

```python
# Store information in memory
await kernel.memory.save_information_async(
    collection="user_conversations",
    id=f"user_{user_id}_conversation_{conversation_id}",
    text="The user asked about deployment processes.",
    description="Conversation about deployment"
)

# Retrieve information from memory
memories = await kernel.memory.search_async(
    collection="user_conversations",
    query="deployment processes",
    limit=5
)

for memory in memories:
    print(f"Relevance: {memory.relevance}, Text: {memory.text}")
```

## 6. Using Skills

### Documentation Navigator Skill

```python
# Search for documentation
result = await kernel.run_async(
    doc_navigator.search_documentation,
    input_str="How do I deploy to production?"
)
print(result)
```

### Code Understanding Skill

```python
# Explain code
code_snippet = """
def process_data(data):
    return [x * 2 for x in data if x > 0]
"""

result = await kernel.run_async(
    code_understanding.explain_code,
    input_str=code_snippet
)
print(result)
```

### Knowledge Gap Analyzer Skill

```python
# Analyze knowledge gaps
result = await kernel.run_async(
    knowledge_analyzer.analyze_knowledge,
    input_str="I'm trying to understand our authentication system"
)
print(result)
```

## 7. Agent Orchestration

The agent orchestration layer routes requests to the appropriate skills:

```python
from konveyor.core.chat.orchestration import AgentOrchestrator

# Initialize the orchestrator
orchestrator = AgentOrchestrator(kernel)

# Process a user message
response = await orchestrator.process_message(
    user_id="user123",
    message="Can you explain how our authentication system works?",
    conversation_id="conv456"
)
print(response)
```

## 8. Next Steps

- Implement persistent memory using Azure Cognitive Search
- Add additional skills for specialized knowledge domains
- Enhance the agent orchestration with more sophisticated routing
- Implement feedback collection and continuous improvement
