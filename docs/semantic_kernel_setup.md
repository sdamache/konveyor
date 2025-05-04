# Semantic Kernel Setup and Usage

## 1. Directory Structure

- `konveyor/skills/` contains Semantic Kernel modules:
  - `__init__.py`: Package initialization.
  - `setup.py`: Core Kernel creation and Azure OpenAI integration.

## 2. Installation

Install Semantic Kernel SDK:
```bash
pip install semantic-kernel
```

## 3. Configuration

Set required environment variables (or store secrets in Key Vault):

- `AZURE_OPENAI_ENDPOINT`: Azure OpenAI endpoint URL.
- `AZURE_OPENAI_API_KEY`: Secret name in Key Vault or direct API key.
- `AZURE_OPENAI_CHAT_DEPLOYMENT`: (optional) deployment name (default: `gpt-35-turbo`).
- `AZURE_OPENAI_API_VERSION`: (optional) API version (default: `2024-12-01-preview`).

## 4. Usage Example

```python
from konveyor.skills.setup import create_kernel

# Initialize kernel
kernel = create_kernel()

# Access chat AI service
chat = kernel.get_service('chat')
response = chat.generate('Hello Semantic Kernel')
print(response)
```

## 5. Memory Configuration

By default, a volatile memory store is added:
```python
mem = kernel.get_memory_store('volatile')
mem.save('key', 'value')
print(mem.get('key'))  # 'value'
```

## 6. Next Steps

- Add skill modules under `konveyor/skills/`.
- Configure persistent memory stores for production.
