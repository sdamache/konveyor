# RAG App: Core Relationship & Modernization Analysis

## Overview
This document outlines the relationship between the `apps/rag/` code and the modular `core/` utilities, highlighting areas for further modernization and cleanup as part of the refactoring plan. The goal is to ensure the RAG app acts as a thin wrapper, delegating core logic to the appropriate modules.

---

## 1. Relationship Between RAG App and Core Modules

- **ConversationManager** (`apps/rag/models.py`) and **ConversationViewSet** (`apps/rag/views.py`) should delegate all Azure storage, retrieval, RAG processing, and prompt management logic to the `core/` modules.
- Key core dependencies observed in `apps/rag/`:
    - `konveyor.core.conversation.storage.AzureStorageManager`: Centralized conversation/message storage and retrieval, used by `ConversationManager`.
    - `konveyor.core.rag.rag_service.RAGService`: Handles the end-to-end RAG process including context retrieval, prompt formatting, and generation, used by `ConversationViewSet`. This service likely utilizes `RAGPromptManager` internally.
    - `konveyor.core.azure_utils.client_manager.AzureClientManager`: Centralized Azure client creation, used by `ConversationViewSet` (likely via `RAGService` and `AzureStorageManager`).
    - `konveyor.core.azure_utils.config.AzureConfig`: Environment/config management (likely used indirectly via core services).
    - `konveyor.core.azure_utils.mixins`: Logging, client setup (likely used indirectly via core services).
    - `konveyor.core.azure_utils.retry`: Robust retry logic (likely used indirectly via core services).

---

## 2. Modernization & Cleanup Recommendations

- **Remove Legacy Logic:**
    - Ensure all conversation storage and retrieval operations in `apps/rag/models.py` strictly use `core.conversation.storage.AzureStorageManager`.
    - Ensure all RAG processing (context fetching, prompt generation, LLM interaction) in `apps/rag/views.py` is handled exclusively by `core.rag.rag_service.RAGService`.
    - Eliminate any direct Azure SDK usage, custom context/prompt logic, or manual configuration handling in `apps/rag/` that is now managed by `core/` modules.

- **Thin Wrappers Only:**
    - Ensure `ConversationManager` and `ConversationViewSet` act as thin wrappers, primarily handling Django request/response cycles and orchestrating calls to core services.
    - All significant business logic, error handling, and validation related to Azure resources or RAG processes should reside within the `core/` modules. Leverage core mixins like `ServiceLoggingMixin` where applicable if services inherit from `AzureService`.

- **Consistent Imports:**
    - Update all imports in `apps/rag/` to use the modular core code paths.
    - Remove any redundant utility or SDK imports now handled by core adapters/services.

- **Testing:**
    - After any cleanup, run all relevant unit/integration tests to ensure no regressions.
    - Add/expand tests specifically verifying the correct delegation of responsibilities from `apps/rag/` to the `core/` utilities (`AzureStorageManager`, `RAGService`).

---

## 3. Relationship to Core Module

The RAG app (`apps/rag/`) should function as a thin adapter layer over the core `AzureStorageManager` and `RAGService`. All business logic for conversation storage, retrieval, and the RAG pipeline (prompt management, context retrieval, generation) must be delegated to the core layer. Any legacy or redundant logic within the app-layer should be removed as part of modernization.

### Function Relationship Table

| App-Layer Component/Function        | Core Equivalent Function/Service                               | Modernization Action                                         |
|-------------------------------------|----------------------------------------------------------------|--------------------------------------------------------------|
| `ConversationManager.create_conversation` | `core.conversation.storage.AzureStorageManager.create_conversation` | Delegate call directly to core; remove redundant app logic |
| `ConversationManager.add_message`         | `core.conversation.storage.AzureStorageManager.add_message`        | Delegate call directly to core; remove redundant app logic |
| `ConversationManager.get_conversation_messages` | `core.conversation.storage.AzureStorageManager.get_conversation_messages` | Delegate call directly to core; remove redundant app logic |
| `ConversationViewSet.ask` (RAG logic) | `core.rag.rag_service.RAGService.generate_response`            | Delegate RAG processing to core service; remove custom logic |
| `ConversationViewSet.create`        | Uses `ConversationManager.create_conversation`                 | Ensure manager delegates correctly as per above              |
| `ConversationViewSet.history`       | Uses `ConversationManager.get_conversation_messages`           | Ensure manager delegates correctly as per above              |

**Note:**
- All conversation storage and retrieval operations in the app-layer must delegate to `core.conversation.storage.AzureStorageManager`.
- All RAG pipeline operations (prompting, context, generation) must delegate to `core.rag.rag_service.RAGService`.
- Remove any direct Azure SDK usage or redundant logic from the app-layer.
- The app-layer should primarily provide Django integration (views, serializers, URLs) and request validation, not duplicate core business logic.

---

## 4. Modernization Progress (as of YYYY-MM-DD)

*(This section should be updated as specific refactoring tasks are completed)*

- **Initial State:** The `apps/rag/` components (`ConversationManager`, `ConversationViewSet`) appear to correctly delegate storage to `AzureStorageManager` and RAG logic to `RAGService`.
- **Completed:**
    - [List completed refactoring steps here, e.g., "Removed direct os.getenv calls..."]
- **Next Steps:**
    - Conduct a detailed audit to confirm no legacy logic remains.
    - Enhance test coverage for delegation verification.

---

## 5. Next Steps

1.  Perform a detailed audit of `apps/rag/models.py` and `apps/rag/views.py` to confirm strict adherence to the delegation principles outlined above.
2.  Identify and remove any remaining direct Azure SDK/config usage or legacy prompt/context management logic.
3.  Refactor any identified areas to use the core adapters/utilities (`AzureStorageManager`, `RAGService`).
4.  Update and run tests to ensure correctness and verify delegation.
5.  Keep this document updated as modernization progresses, particularly the "Modernization Progress" section.
6.  Ensure architectural diagrams and other documentation align with the code changes.

---

## 6. References

- See `docs/architecture.md` for the full class/function breakdown (ensure it's updated).
- See `docs/refactoring_plan.md` for the phased refactoring steps.

---

*This document should be updated iteratively as you proceed with the systematic cleanup and modernization of the RAG app.*
