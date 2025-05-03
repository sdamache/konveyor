
# Konveyor AI Agents Hackathon – Research Notes (Tasks 2 – 5)

Scope – Concise, working snippets + pitfalls for each sub-task; all code shown is only the delta you need to add.

## Task 2 – Set up Semantic Kernel Framework (feat/task-2-semantic-kernel-setup)

2.1 Directory Skeleton

```
konveyor/
 └─ skills/                   # new root for SK skills
    └─ <SkillName>/           # PascalCase, one dir per skill
tests/
```

Keep every `__init__.py` minimal – SK’s loader relies on package discovery.

2.2 Install & Bootstrap

```python
pip install --upgrade "semantic-kernel[azure]==1.0.1"
```

1.0.1 is the current GA Python release.

```python
from semantic_kernel import Kernel
kernel = Kernel()
```

2.3 Wire Azure OpenAI with Key Vault

```python
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from semantic_kernel.connectors.ai.azure_ai_inference import AzureAIInferenceChatCompletion

vault_uri = f"https://{os.getenv('KEY_VAULT_NAME')}.vault.azure.net"
secret_cli = SecretClient(vault_uri, DefaultAzureCredential())

api_key  = secret_cli.get_secret("AZURE_OPENAI_KEY").value
endpoint = secret_cli.get_secret("AZURE_OPENAI_ENDPOINT").value

chat = AzureAIInferenceChatCompletion(
    ai_model_id="gpt-4o-vision-preview",
    api_key=api_key,
    endpoint=endpoint,
)
kernel.add_service(chat)
```

Grant secrets/get + secrets/list to your app registration; don’t hard-code the full deployment URL – the connector builds it.

2.4 Volatile Memory

```python
from semantic_kernel.connectors.memory.volatile import VolatileStore
kernel.register_memory_store(VolatileStore())
```

Pure in-proc cache – restart wipes it; good for fast prototyping.

2.5 Common Pitfalls

Symptom	Root cause	Quick fix
ValueError: service already exists	Multiple add_service() calls	Wrap in if not kernel.has_service(...)
401 from OpenAI	KV secret contains deployment key instead of resource key	Store the resource key
aiohttp.client_exceptions.ServerDisconnectedError	Missing asyncio.run(...) around SK call	Make top-level handlers async



## Task 3 – Agent Orchestration Layer (feat/task-3-agent-orchestration)

3.1 Slack Entry-Point

```python
from slack_bolt.async_app import AsyncApp
app = AsyncApp(token=os.getenv("SLACK_BOT_TOKEN"),
               signing_secret=os.getenv("SLACK_SIGNING_SECRET"))


@app.event("app_mention")
async def on_mention(body, say):
    text = body["event"]["text"]
    reply = await orchestrate(text)
    await say(reply)
```

3.2 Skill Routing (rule-based seed)

```python
ROUTES = {"docs": "DocumentationNavigatorSkill",
          "explain": "CodeUnderstandingSkill"}

async def orchestrate(text: str) -> str:
    for kw, skill in ROUTES.items():
        if kw in text.lower():
            return await kernel.invoke(skill, "run", text=text)
    return "Sorry, I’m not trained for that yet."
```

Upgrade later with embeddings cosine-sim intent mapping.

3.3 Error & Log Wrapper

```python
import structlog
log = structlog.get_logger()
try:
    out = await kernel.invoke(...)
except Exception as exc:
    log.exception("skill_error", err=str(exc))
    out = "I hit a snag – try again?"
```

3.4 Slack Event Scopes & Limits
	•	Subscribe to app_mention, message.channels, reaction_added.
	•	Slack hard-limits messages to ~4 kB – truncate or stream.

## Task 4 – Documentation Navigator Skill (feat/task-4-documentation-navigator)

4.1 Skill Shell

```python
from semantic_kernel.functions import kernel_function
class DocumentationNavigatorSkill:
    def __init__(self, search):
        self.search = search

    @kernel_function(description="Search docs and return hits")
    async def run(self, text: str):
        return await self.search.query(text)
```
4.2 Query Pre-processing & Slack Markdown
•	Strip trailing ?, expand acronyms (e.g., “AKS”→“Azure Kubernetes Service”).
•	Slack list format:

    • *Title* — <url>

    • Multi-line responses: wrap in triple back-ticks.

4.3 Conversation Memory

```python
await kernel.memory.save(collection="docs",
                         key=user_id,
                         data=text)
```

Stores last queries for follow-ups.

## Task 5 – Code Understanding Skill (feat/task-5-code-understanding)

5.1 Language Detection

```python
from pygments.lexers import guess_lexer
from pygments.util import ClassNotFound

def detect_lang(code: str) -> str:
    try:
        return guess_lexer(code).name
    except ClassNotFound:
        return "text"
```

5.2 Prompt Template

```python
{{code}}
----
Explain purpose, inputs, side-effects, and highlight anti-patterns.
Return Markdown.
```

5.3 Slack Syntax-Highlighted Reply

```python
reply = f"```{lang.lower()}\n{code}\n```\n{explanation}"
```

Slack auto-highlights with the language tag.

5.4 Error Handling & Size Guard
•	Catch ClassNotFound → treat as plain text.
•	If snippet > 3500 chars → upload as file & return link.

## Reference Index

Sub-task	Key sources
2.2 Install	Semantic Kernel release notes
2.3 Azure OpenAI + KV	Azure quick-start doc
2.4 Volatile Store	Volatile connector docs
3.4 Slack scopes & events	reaction_added & Events API docs
4.x Slack md & blocks	Slack formatting guide
5.1 Pygments	Quick-start & API docs

Additional inspiration & code walk-throughs: SK Cookbook, sample agents, etc.

## Next steps:
If you'd like me to expand any section (e.g., async streaming, CI harness, embedding router), just call it out and I'll append an update.
