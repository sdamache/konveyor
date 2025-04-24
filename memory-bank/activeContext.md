# Active Context: Konveyor

## Current Work Focus

- Azure infrastructure provisioning (App Service, Key Vault, Cognitive Search, OpenAI, etc.) and CI/CD pipeline setup are implemented via Terraform and GitHub Actions (task-1).
- Pending validation of Azure App Service deployment and end-to-end connectivity.
- Next focus: complete and test agent orchestration layer, integrate Semantic Kernel skills (Documentation Navigator, Code Understanding, Knowledge Gap Analyzer), and finalize Slack/Bot Framework integration.
- Enhance CI/CD for integration testing and automated deployment.
- All retrieval and context for the current demo are handled via Azure Cognitive Search; Redis cache and Cosmos DB are not yet active and are planned for future cost optimization.
- Task plan from tasks.json is the authoritative roadmap for all further development.

## Recent Changes

- Infrastructure-as-Code (Terraform) modules for all required Azure resources are implemented and active.
- GitHub Actions workflow for CI/CD (build and deploy to Azure App Service) is present and configured.
- Core Django modules for documents, search, RAG, and utilities are in place and functional.
- Azure Cognitive Search is integrated and operational for RAG workflows.
- Test scaffolding exists for core workflows, but end-to-end and user journey tests are not yet implemented.
- Memory bank is now aligned with the current branch and the task-master plan.

## Next Steps

- Deploy the Django application to Azure App Service and validate end-to-end Azure integration.
- Complete and test the agent orchestration layer and Semantic Kernel skills.
- Finalize and test Slack/Bot Framework integration.
- Enhance CI/CD for automated deployment and integration testing.
- Implement end-to-end and user journey tests.
- Follow the detailed implementation plan and task breakdown in the tasks folder and scripts/prd_draft_for_ai.txt to complete the MVP.

## Active Decisions and Considerations

- Azure AI Search is the only active backend for retrieval and context in the current demo; Redis and Cosmos DB are deferred for future optimization.
- Bot integration and App Service deployment are the highest priorities for enabling full system functionality and demo readiness.
- The project roadmap and next steps are managed via the tasks folder and PRD draft, which should be followed for structured, AI-driven implementation.

## Learnings and Project Insights

- Focusing on Azure AI Search for the initial demo accelerates development but will require future migration to Redis/Cosmos DB for cost and performance.
- Modular infrastructure and codebase design support phased rollout and future extensibility.
- Structured task management and clear development roadmap are critical for coordinating agentic and cloud-native features.
