# Project Brief: Konveyor

Konveyor is an AI-powered knowledge transfer (KT) agent designed specifically to accelerate the onboarding and productivity of software engineers. The project addresses the most significant pain points faced by engineering teams during onboarding and knowledge transfer, as identified through industry research and practitioner feedback.

## Core Requirements and Goals

- Provide software engineers with fast, context-aware answers about codebases, architecture, and engineering processes.
- Bridge gaps in documentation by synthesizing information from code, documents, and tribal knowledge.
- Enable engineers to search and query across fragmented knowledge sources (code, docs, chat, wikis) from a single interface.
- Support structured onboarding by surfacing relevant context, design decisions, and setup instructions.
- Reduce reliance on senior engineers for repetitive onboarding questions, freeing them for higher-value work.
- Integrate with existing engineering tools and platforms (e.g., code repositories, documentation, chat).

## Key Problems Addressed

- Lack of comprehensive, up-to-date, and centralized documentation.
- Knowledge silos and ineffective handover processes.
- Overwhelming or unstructured onboarding experiences.
- Difficulty understanding complex, undocumented codebases.
- Limited access to mentorship and context from senior engineers.
- Communication barriers in remote and cross-team environments.
- Inadequate search and fragmented tool integration for engineering knowledge.

## Solution Approach

- Use LLMs to understand and answer context-specific engineering questions.
- Ingest and index codebases, documentation, and other knowledge sources.
- Provide architectural overviews, design rationale, and actionable onboarding steps.
- Integrate with chat platforms (e.g., Teams) for conversational access.
- Support both passive (documentation) and active (how-to, context-specific) knowledge delivery.

## Technology Stack

- Python 3.10+, Django web framework.
- Azure OpenAI for LLM-powered responses.
- PostgreSQL (production) / SQLite (development).
- Azure services: Key Vault, Blob Storage, App Service, Application Insights.
- Containerization and CI/CD planned (Docker, GitHub Actions).

## Source of Truth

This document defines the core requirements, goals, and scope for the Konveyor project, with a focus on solving onboarding and knowledge transfer challenges for software engineers.
