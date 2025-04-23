# Azure Infrastructure Setup

This document provides an overview of the Azure infrastructure setup for the Konveyor project.

## Resources Provisioned

The following Azure resources have been provisioned using Terraform:

- **Resource Group**: Contains all resources for the project
- **App Service**: Hosts the Django application
- **Key Vault**: Securely stores credentials and secrets
- **OpenAI**: Provides AI capabilities for the application
- **Document Intelligence**: Processes and analyzes documents
- **Storage Account**: Stores application data and files
- **Cognitive Search**: Enables search functionality
- **Bot Service**: Supports the Slack bot integration

## CI/CD Pipeline

The CI/CD pipeline is implemented using GitHub Actions:

- **Docker Build**: Builds the application container
- **Container Registry**: Stores container images in GitHub Container Registry (ghcr.io)
- **Deployment**: Deploys the container to Azure App Service
- **Conventions**: Enforces branch naming and commit message conventions

## Health Checks

A health check endpoint is available at `/healthz/` that verifies:

- Database connectivity
- Critical service availability
- Application status

## Local Development

To run the application locally:

```bash
# Development environment
docker-compose up konveyor-dev

# Production-like environment
docker-compose up konveyor-prod
```

## Troubleshooting

Common issues and solutions:

- **SSL Redirect Loop**: Fixed by disabling SSL redirect in Azure App Service
- **Asyncio Syntax Error**: Resolved by removing the package at runtime
- **Database Connectivity**: Implemented SQLite fallback for local testing
