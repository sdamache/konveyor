# Semantic Kernel Skills for Konveyor

This directory contains the Semantic Kernel skills used by the Konveyor project.

## Overview

Semantic Kernel is a lightweight SDK that integrates Large Language Models (LLMs) with conventional programming languages. In Konveyor, we use Semantic Kernel to create AI-powered skills that can be used by the agent orchestration layer to respond to user requests.

## Directory Structure

- `__init__.py` - Package initialization
- `setup.py` - Core setup for Semantic Kernel
- `BasicSkill.py` - A simple demonstration skill
- `ChatSkill.py` - A skill for chat interactions
- `documentation_navigator/` - Documentation search and retrieval skill
  - `DocumentationNavigatorSkill.py` - Main implementation
  - `README.md` - Documentation and usage examples
- `examples/` - Example scripts showing how to use the skills

## Skills

### BasicSkill

A simple skill that demonstrates the basic structure of a Semantic Kernel skill. It provides functions for:

- Greeting a user
- Formatting text as a bullet list

### ChatSkill

A more advanced skill for chat interactions. It provides functions for:

- Answering questions
- Maintaining conversation context
- Formatting responses for Slack

### DocumentationNavigatorSkill

A skill for documentation search and retrieval that wraps the existing SearchService. It provides functions for:

- Searching documentation using natural language queries
- Preprocessing queries for better search results
- Answering questions using documentation
- Maintaining conversation context across interactions
- Handling follow-up questions with contextual awareness
- Formatting responses with citations
- Formatting results for Slack

The skill integrates with the conversation memory system to maintain context across interactions, allowing for more natural, contextual conversations about documentation.

For more details, see the [DocumentationNavigatorSkill README](documentation_navigator/README.md).

## Usage

### Creating a Kernel

```python
from konveyor.skills.setup import create_kernel

# Create a kernel with chat service
kernel = create_kernel()

# Create a kernel with both chat and embedding services
kernel_with_embeddings = create_kernel(use_embeddings=True)
```

### Using a Skill

#### ChatSkill Example

```python
from konveyor.skills.setup import create_kernel
from konveyor.skills.ChatSkill import ChatSkill

# Create a kernel
kernel = create_kernel()

# Import the ChatSkill
chat_skill = ChatSkill()
functions = kernel.add_plugin(chat_skill, plugin_name="chat")

# Use the answer_question function
question = "What is Semantic Kernel?"
answer = kernel.run_function(
    functions["answer_question"],
    input_str=question
)
print(answer)
```

#### DocumentationNavigatorSkill Example

```python
import asyncio
from konveyor.skills.setup import create_kernel
from konveyor.skills.documentation_navigator import DocumentationNavigatorSkill

async def search_docs():
    # Create a kernel
    kernel = create_kernel()

    # Import the DocumentationNavigatorSkill
    doc_skill = DocumentationNavigatorSkill(kernel)
    functions = kernel.add_plugin(doc_skill, plugin_name="documentation")

    # Search for documentation
    query = "How do I set up my development environment?"
    result = await functions["search_documentation"].invoke(query=query)
    print(f"Found {result['result_count']} results")

    # Answer a question
    answer = await functions["answer_question"].invoke(question=query)
    print(f"Answer: {answer[:100]}...")

# Run the example
asyncio.run(search_docs())
```

#### Contextual Conversation Example

```python
import asyncio
from konveyor.skills.setup import create_kernel
from konveyor.skills.documentation_navigator import DocumentationNavigatorSkill

async def contextual_conversation():
    # Create a kernel
    kernel = create_kernel()

    # Create the DocumentationNavigatorSkill
    doc_skill = DocumentationNavigatorSkill(kernel)
    functions = kernel.add_plugin(doc_skill, plugin_name="documentation")

    # Create a new conversation
    conversation = await functions["create_conversation"].invoke()
    conversation_id = conversation["id"]
    print(f"Created conversation: {conversation_id}")

    # Ask an initial question
    initial_question = "What is the onboarding process?"
    answer1 = await functions["answer_question"].invoke(
        question=initial_question,
        conversation_id=conversation_id
    )
    print(f"Initial answer: {answer1[:100]}...")

    # Ask a follow-up question
    follow_up = "What should I do on my first day?"
    answer2 = await functions["continue_conversation"].invoke(
        follow_up_question=follow_up,
        conversation_id=conversation_id
    )
    print(f"Follow-up answer: {answer2[:100]}...")

# Run the example
asyncio.run(contextual_conversation())
```

### Running Examples

```bash
# Activate the virtual environment
source venv/bin/activate

# Set Azure OpenAI credentials
export AZURE_OPENAI_ENDPOINT="https://your-endpoint.openai.azure.com"
export AZURE_OPENAI_API_KEY="your-api-key"
export AZURE_OPENAI_CHAT_DEPLOYMENT="gpt-35-turbo"

# Run the chat example
python -m konveyor.skills.examples.chat_example

# For DocumentationNavigatorSkill, you can create a script using the example above
# and run it directly
```

### Registering with Agent Orchestrator

To register the DocumentationNavigatorSkill with the agent orchestrator:

```python
import asyncio
from konveyor.skills.setup import create_kernel
from konveyor.skills.documentation_navigator import DocumentationNavigatorSkill
from konveyor.skills.agent_orchestrator.AgentOrchestratorSkill import AgentOrchestratorSkill
from konveyor.skills.agent_orchestrator.registry import SkillRegistry

async def register_skill():
    # Create kernel and registry
    kernel = create_kernel()
    registry = SkillRegistry()

    # Create skills
    doc_skill = DocumentationNavigatorSkill(kernel)
    orchestrator = AgentOrchestratorSkill(kernel, registry)

    # Register the DocumentationNavigatorSkill
    skill_name = orchestrator.register_skill(
        doc_skill,
        description="A skill for searching and navigating documentation",
        keywords=["documentation", "search", "help", "guide", "onboarding"]
    )

    print(f"Registered skill as: {skill_name}")

    # Test with a query
    response = await orchestrator.process_request(
        "Where can I find documentation about onboarding?"
    )
    print(f"Response: {response}")

# Run the registration
asyncio.run(register_skill())
```

## Creating New Skills

To create a new skill:

1. Create a new file in the `konveyor/skills/` directory with a PascalCase name (e.g., `DocumentationNavigatorSkill.py`)
2. Define a class with the same name as the file
3. Add functions decorated with `@kernel_function`
4. Import and use the skill as shown in the examples

Example:

```python
from semantic_kernel.functions import kernel_function

class MyNewSkill:
    @kernel_function(
        description="Description of what this function does",
        name="function_name"
    )
    def function_name(self, input: str) -> str:
        # Function implementation
        return f"Processed: {input}"
```

## Testing

Skills can be tested using the pytest framework. See `tests/test_chat_skill.py` for an example of how to test skills with both real Azure OpenAI credentials and mocks for CI/CD environments.

## Environment Variables

The following environment variables are used by the Semantic Kernel setup:

- `AZURE_OPENAI_ENDPOINT` - The endpoint URL for Azure OpenAI
- `AZURE_OPENAI_API_KEY` - The API key for Azure OpenAI
- `AZURE_OPENAI_CHAT_DEPLOYMENT` - The deployment name for chat completions (default: "gpt-35-turbo")
- `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` - The deployment name for embeddings (default: "text-embedding-ada-002")
- `AZURE_OPENAI_API_VERSION` - The API version to use (default: "2024-12-01-preview")
- `AZURE_KEY_VAULT_NAME` - The name of the Azure Key Vault (optional, for secure key storage)
