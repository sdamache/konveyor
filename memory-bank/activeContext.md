# Active Context: Konveyor

## Current Work Focus

- Completing Azure App Service deployment for the Django application to enable full Azure integration and production readiness.
- Implementing and integrating the agent orchestration layer for routing requests to Semantic Kernel skills/tools.
- Developing and integrating Semantic Kernel skills: Documentation Navigator, Code Understanding, and Knowledge Gap Analyzer.
- Finalizing Slack/Bot Framework integration to enable chat-based access to the agent.
- Enhancing CI/CD pipeline for integration testing and automated deployment.
- All retrieval and context for the current demo are handled via Azure Cognitive Search; Redis cache and Cosmos DB are not yet active and are planned for future cost optimization.

## Recent Changes

- Core Django modules for documents, search, RAG, and utilities are in place and functional.
- Azure Cognitive Search is integrated and operational for RAG workflows.
- Infrastructure-as-Code (Terraform) provisions most required Azure resources, but App Service deployment is still pending.
- Test scaffolding exists for core workflows, but end-to-end and user journey tests are not yet implemented.

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
