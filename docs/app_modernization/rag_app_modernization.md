# RAG App: Core Relationship & Modernization Analysis

## Overview
This document outlines the relationship between the `apps/rag/` code and the modular `core/` utilities, highlighting areas for further modernization and cleanup as part of the refactoring plan.

---

## 1. Relationship Between RAG App and Core Modules

- **ConversationManager** and **ConversationViewSet** in `apps/rag/` should delegate all Azure storage, retrieval, and prompt management logic to the `core/` modules.
- Key core dependencies:
    - `core/conversation/storage.py` → `AzureStorageManager` (centralized conversation/message storage)
    - `core/rag/templates.py` → `RAGPromptManager`, `PromptTemplate` (prompt template management)
    - `core/azure_utils/clients.py` → `AzureClientManager` (centralized Azure client creation)
    - `core/azure_utils/config.py` → `AzureConfig` (environment/config management)
    - `core/azure_utils/mixins.py` → Logging, client setup
    - `core/azure_utils/retry.py` → Robust retry logic

---

## 2. Modernization & Cleanup Recommendations

- **Remove Legacy Logic:**
    - Ensure all conversation storage, retrieval, and prompt handling use the core managers/utilities.
    - Eliminate any direct Azure SDK usage or custom context/prompt logic in `apps/rag/` that is now handled by `core/`.

- **Thin Wrappers Only:**
    - Ensure Django adapters/services in `apps/rag/` act as thin wrappers over the core code.
    - All logging, error handling, and validation should use `ServiceLoggingMixin` and related core utilities.

- **Consistent Imports:**
    - Update all imports in `apps/rag/` to use modular core code.
    - Remove any old utility or SDK imports now handled by core adapters.

- **Testing:**
    - After each cleanup, run all unit/integration tests to ensure no regressions.
    - Add/expand tests to verify correct delegation to core utilities.

---

## Relationship to Core Module

The RAG app should act as a thin adapter/wrapper over the core `AzureStorageManager`, `RAGPromptManager`, and related utilities. All business logic for conversation storage, retrieval, and prompt management must be delegated to the core layer. Any legacy or redundant logic in the app-layer should be removed as part of modernization.

### Function Relationship Table

| App-Layer Function Name         | Core Equivalent Function                                   | Modernization Action                                   |
|---------------------------------|------------------------------------------------------------|--------------------------------------------------------|
| `create_conversation`           | `core.conversation.storage.AzureStorageManager.create_conversation` | Delegate call directly to core; remove app logic      |
| `add_message`                   | `core.conversation.storage.AzureStorageManager.add_message`        | Delegate to core; remove redundant app logic           |
| `get_conversation_messages`     | `core.conversation.storage.AzureStorageManager.get_conversation_messages` | Delegate to core; remove redundant app logic |
| `ask` (prompt handling)         | `core.rag.templates.RAGPromptManager.format_prompt`                | Delegate to core; remove custom prompt/context logic   |
| `get_template`                  | `core.rag.templates.RAGPromptManager.get_template`                | Delegate to core; remove redundant app logic           |
| `add_template`                  | `core.rag.templates.RAGPromptManager.add_template`                | Delegate to core; remove redundant app logic           |

**Note:**
- All conversation storage, retrieval, and prompt management operations in the app-layer must delegate to the core equivalents listed above.
- Remove any direct Azure SDK usage or redundant logic from the app-layer.
- The app-layer should only provide Django integration or request validation, not duplicate business logic.

---

## 3. Next Steps

1. Audit each function in `apps/rag/` for direct Azure SDK/config usage or legacy prompt/context management.
2. Refactor to use core adapters/utilities, removing legacy code.
3. Keep this document updated as modernization progresses.
4. Sync architectural diagrams and documentation with code changes.

---

## References
- See `docs/architecture.md` for the full class/function breakdown.
- See `docs/refactoring_plan.md` for the phased refactoring steps.

---

*This document should be updated iteratively as you proceed with the systematic cleanup and modernization of the RAG app.*
