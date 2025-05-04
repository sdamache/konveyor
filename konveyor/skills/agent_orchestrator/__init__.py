"""
Agent Orchestrator package for Konveyor.

This package provides the orchestration layer for routing requests to appropriate
Semantic Kernel skills and tools. It handles request analysis, skill selection,
and response formatting.

This module provides proxy imports for the AgentOrchestratorSkill and SkillRegistry classes,  # noqa: E501
which have been moved to konveyor.core.agent.
"""

import logging

from konveyor.core.agent.orchestrator import AgentOrchestratorSkill
from konveyor.core.agent.registry import SkillRegistry

# Configure logging
logger = logging.getLogger(__name__)
logger.info("Using AgentOrchestratorSkill and SkillRegistry from konveyor.core.agent")

__all__ = ["AgentOrchestratorSkill", "SkillRegistry"]
