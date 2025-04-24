# Semantic Kernel Skills for Konveyor

This directory contains the Semantic Kernel skills used by the Konveyor project.

## Overview

Semantic Kernel is a lightweight SDK that integrates Large Language Models (LLMs) with conventional programming languages. In Konveyor, we use Semantic Kernel to create AI-powered skills that can be used by the agent orchestration layer to respond to user requests.

## Directory Structure

- `__init__.py` - Package initialization
- `setup.py` - Core setup for Semantic Kernel
- `BasicSkill.py` - A simple demonstration skill
- `ChatSkill.py` - A skill for chat interactions
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
