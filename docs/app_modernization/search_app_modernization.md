# Search App: Core Relationship & Modernization Analysis

## Overview
This document details the relationship between the `apps/search/` code and the modular `core/` utilities, highlighting areas for further modernization and cleanup as part of the ongoing refactoring plan.

---

## 1. Relationship Between Search App and Core Modules

- **IndexingService** and **SearchService** in `apps/search/services/` are designed as orchestration layers.
    - They should delegate all Azure SDK calls, configuration, logging, and retry logic to the `core/` modules.
    - Key core dependencies:
        - `core/azure/service.py` → `AzureService` (base class for config/logging/client management)
        - `core/azure_adapters/openai/client.py` → `AzureOpenAIClient` (embeddings/completions)
        - `core/azure_utils/clients.py` → `AzureClientManager` (centralized Azure client creation)
        - `core/azure_utils/config.py` → `AzureConfig` (environment/config management)
        - `core/azure_utils/mixins.py` → Logging, client setup
        - `core/azure_utils/retry.py` → Robust retry logic

---

## 2. Modernization & Cleanup Recommendations

- **Remove Legacy Logic:**
    - Eliminate any direct Azure SDK usage, custom retry, or config parsing in `apps/search/` that duplicates core functionality.
    - Refactor all Azure operations (embedding, search, index management) to use `AzureOpenAIClient`, `AzureClientManager`, and `AzureService`.
    - Remove redundant or legacy methods (e.g., custom semantic search if hybrid_search is canonical).

- **Thin Wrappers Only:**
    - Ensure `IndexingService` and `SearchService` act as thin adapters—no business logic or error handling that should reside in core.
    - All logging, error handling, and validation should use `ServiceLoggingMixin` and related core utilities.

- **Consistent Imports:**
    - Update all imports in `apps/search/` to use the new modular core code.
    - Remove any old utility or SDK imports that are now handled by core adapters.

- **Testing:**
    - After each cleanup, run all unit/integration tests to ensure no regressions.
    - Add/expand tests to verify correct delegation to core utilities.

---

## Relationship to Core Module

The search app should act as a thin adapter/wrapper over the core `AzureOpenAIClient`, `AzureService`, and related utilities. All business logic for embedding generation, search, and index management must be delegated to the core layer. Any legacy or redundant logic in the app-layer should be removed as part of modernization.

### Function Relationship Table

| App-Layer Function Name         | Core Equivalent Function                       | Modernization Action                                   |
|---------------------------------|------------------------------------------------|--------------------------------------------------------|
| `generate_embedding`            | `core.azure_adapters.openai.client.generate_embedding` | Delegate call directly to core; remove app logic      |
| `hybrid_search`                 | (core utility or adapter, if exists)           | Delegate to core or refactor to use core utilities     |
| `semantic_search`               | (core utility or adapter, if exists)           | Remove if redundant; use core for embedding/search     |
| `vector_similarity_search`      | (core utility or adapter, if exists)           | Remove if redundant; use core for vector search        |
| `index_document_chunk`          | (core utility or adapter, if exists)           | Delegate to core; remove redundant app logic           |
| `get_chunk_content`             | `core.documents.document_service.get_chunk_content` | Delegate to core; remove redundant app logic     |
| `create_search_index`           | `core utility or adapter, if exists`           | Delegate to core; remove redundant app logic           |
| `delete_index`                  | `core utility or adapter, if exists`           | Delegate to core; remove redundant app logic           |
| `get_index`                     | `core utility or adapter, if exists`           | Delegate to core; remove redundant app logic           |

**Note:**
- All embedding, search, and index management operations in the app-layer must delegate to the core equivalents listed above.
- Remove any direct Azure SDK usage or redundant logic from the app-layer.
- The app-layer should only provide Django integration or request validation, not duplicate business logic.

---

## 3. Next Steps

1. Audit each function in `apps/search/services/` for direct Azure SDK/config usage.
2. Refactor to use core adapters/utilities, removing legacy code.
3. Keep this document updated as modernization progresses.
4. Sync architectural diagrams and documentation with code changes.

---

## References
- See `docs/architecture.md` for the full class/function breakdown.
- See `docs/refactoring_plan.md` for the phased refactoring steps.

---

*This document should be updated iteratively as you proceed with the systematic cleanup and modernization of the search app.*
