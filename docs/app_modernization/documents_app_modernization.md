# Documents App: Core Relationship & Modernization Analysis

## Overview
This document outlines the relationship between the `apps/documents/` code and the modular `core/` utilities, highlighting areas for further modernization and cleanup as part of the refactoring plan.

---

## 1. Relationship Between Documents App and Core Modules

- **DocumentService**, **DocumentParser**, and related adapters in `apps/documents/services/` should delegate all Azure SDK calls, configuration, logging, and retry logic to the `core/` modules.
- Key core dependencies:
    - `core/azure/service.py` → `AzureService` (base class for config/logging/client management)
    - `core/documents/document_service.py` → `DocumentService` (centralized document parsing, chunking, and storage)
    - `core/azure_utils/clients.py` → `AzureClientManager` (centralized Azure client creation)
    - `core/azure_utils/config.py` → `AzureConfig` (environment/config management)
    - `core/azure_utils/mixins.py` → Logging, client setup
    - `core/azure_utils/retry.py` → Robust retry logic

---

## 2. Modernization & Cleanup Recommendations

- **Remove Legacy Logic:**
    - Legacy parsing methods (e.g., `_parse_pdf`, `_parse_docx`, etc.) still exist in the app-layer `DocumentService`.
    - Full delegation to the core parsing/chunking logic is not yet complete.
    - Action Item: Refactor or remove these methods and ensure all document parsing, chunking, and storage in the app layer uses the core `DocumentService` and `DocumentParser` only.
    - Remove redundant/legacy methods (e.g., those in `document_service.py.bak`).

- **Thin Wrappers Only:**
    - Ensure Django adapters/services in `apps/documents/` act as thin wrappers over the core code.
    - All logging, error handling, and validation should use `ServiceLoggingMixin` and related core utilities.

- **Consistent Imports:**
    - Update all imports in `apps/documents/` to use modular core code.
    - Remove any old utility or SDK imports now handled by core adapters.

- **Testing:**
    - After each cleanup, run all unit/integration tests to ensure no regressions.
    - Add/expand tests to verify correct delegation to core utilities.

---

## Relationship to Core Module

The documents app should act as a thin adapter/wrapper over the core `DocumentService` and related utilities. All business logic for parsing, chunking, and storage must be delegated to the core layer. Any legacy or redundant logic in the app-layer should be removed as part of modernization.

### Function Relationship Table

| App-Layer Function Name         | Core Equivalent Function              | Modernization Action                                   |
|---------------------------------|---------------------------------------|--------------------------------------------------------|
| `parse_file`                    | `core.documents.document_service.parse_file` | Delegate call directly to core; remove app logic      |
| `_parse_pdf`                    | `core.documents.document_service._parse_pdf` | Remove from app; use core for PDF parsing             |
| `_parse_docx`                   | `core.documents.document_service._parse_docx`| Remove from app; use core for DOCX parsing            |
| `_parse_markdown`               | `core.documents.document_service._parse_markdown`| Remove from app; use core for Markdown parsing   |
| `_parse_text`                   | `core.documents.document_service._parse_text` | Remove from app; use core for text parsing            |
| `store_chunk_content`           | `core.documents.document_service.store_chunk_content` | Delegate to core; remove redundant app logic |
| `get_chunk_content`             | `core.documents.document_service.get_chunk_content`   | Delegate to core; remove redundant app logic |

**Note:**
- All parsing, chunking, and storage operations in the app-layer must delegate to the core equivalents listed above.
- Remove any direct Azure SDK usage or redundant logic from the app-layer.
- The app-layer should only provide Django integration or request validation, not duplicate business logic.

---

## 3. Detailed Refactoring Plan (Approved 2025-04-15)

This plan involves two phases: first refactoring the core service for consistency, then refactoring the app layer to use the improved core service.

### Phase A: Refactor Core Service (`konveyor/core/documents/document_service.py`)

1.  **Inheritance:** Change class to inherit from `konveyor.core.azure_utils.service.AzureService`.
2.  **Refactor `__init__`:**
    *   Call `super().__init__('DOCUMENT_INTELLIGENCE')`.
    *   Get clients via `self.client_manager` (e.g., `self.doc_intelligence_client = self.client_manager.get_document_intelligence_client()`).
3.  **Remove Redundant Code:**
    *   Delete manual `AzureClientManager` instantiation.
    *   Delete direct `os.getenv` calls for endpoint/key.
    *   Delete manual validation logic.
    *   Delete `try/except` block around client initialization.
    *   Delete `initialize_document_intelligence_client` method.
4.  **Refactor Storage Methods:** Update `store_chunk_content` and `get_chunk_content` to use `self.config.get_setting('AZURE_STORAGE_CONTAINER_NAME', default='document-chunks')` instead of `os.getenv`.
5.  **Standardize Logging:** Replace `logger.*` calls with `self.log_success`, `self.log_error`, etc.
6.  **Clean Imports:** Remove unused imports (`os`, `AzureKeyCredential`, etc.).

### Phase B: Refactor App Layer (`konveyor/apps/documents/services/*`)

1.  **Simplify/Remove `apps/.../document_service.py`:**
    *   Evaluate if this file can be deleted entirely.
    *   If kept, remove all parsing, storage, search, and helper methods, delegating calls to the core service instance.
    *   Refactor `__init__` to only instantiate the core service if needed for delegation.
    *   Remove internal `DocumentParser` and `BatchProcessor` classes.
    *   Clean up imports drastically.
2.  **Update `apps/.../document_adapter.py`:**
    *   Ensure `__init__` instantiates the *core* `DocumentService` (`konveyor.core.documents.document_service.DocumentService`).
    *   Refactor `process_document` to call the core service for parsing/chunking/storage, receiving necessary data back, and only handling Django model creation/updates.
    *   Remove `_get_content_type` and `_create_chunks` methods.
    *   Clean up imports.
3.  **Delete `.bak` Files:** Remove `document_service.py.bak` from both `core/documents/` and `apps/documents/services/` upon successful completion and testing.

### Implementation Notes:

*   Implement Phase A first, test thoroughly.
*   Then implement Phase B, test thoroughly.
*   Keep this document updated if any deviations from the plan occur during implementation.

---

## References
- See `docs/architecture.md` for the full class/function breakdown.
- See `docs/refactoring_plan.md` for the phased refactoring steps.

---

*This document should be updated iteratively as you proceed with the systematic cleanup and modernization of the documents app.*
