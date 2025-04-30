"""
Skill Registry for Agent Orchestrator.

This module provides a registry for Semantic Kernel skills, allowing the
orchestrator to discover and invoke the appropriate skills based on user requests.
"""

import logging
import sys
from typing import Dict, Any, List, Optional, Type, Set
import inspect
from semantic_kernel.functions import KernelFunction

# Default keywords for built-in skills
DEFAULT_SKILL_KEYWORDS = {
    "DocumentationNavigatorSkill": [
        "documentation",
        "docs",
        "search",
        "find",
        "information",
        "help",
        "guide",
        "manual",
        "reference",
        "lookup",
        "document",
        "article",
        "tutorial",
        "how-to",
        "faq",
        "question",
        "answer",
        "onboarding",
        "getting started",
        "learn",
        "knowledge",
        "info",
    ]
}

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


class SkillRegistry:
    """
    Registry for Semantic Kernel skills.

    This class maintains a registry of available skills and their functions,
    allowing the orchestrator to discover and invoke the appropriate skills
    based on user requests.

    Attributes:
        skills (Dict[str, Any]): Dictionary of registered skills
        skill_descriptions (Dict[str, str]): Descriptions of registered skills
        function_descriptions (Dict[str, Dict[str, str]]): Descriptions of skill functions
        keywords (Dict[str, Set[str]]): Keywords associated with each skill
    """

    def __init__(self):
        """Initialize the skill registry."""
        self.skills: Dict[str, Any] = {}
        self.skill_descriptions: Dict[str, str] = {}
        self.function_descriptions: Dict[str, Dict[str, str]] = {}
        self.keywords: Dict[str, Set[str]] = {}

    def register_skill(
        self,
        skill: Any,
        skill_name: Optional[str] = None,
        description: Optional[str] = None,
        keywords: Optional[List[str]] = None,
    ) -> str:
        """
        Register a skill with the registry.

        Args:
            skill: The skill instance to register
            skill_name: Optional name for the skill (defaults to class name)
            description: Optional description of the skill
            keywords: Optional list of keywords associated with the skill

        Returns:
            The name of the registered skill
        """
        logger.info(f"Registering skill: {skill.__class__.__name__}")

        # Get the skill name if not provided
        if not skill_name:
            skill_name = skill.__class__.__name__
            logger.info(f"Using default skill name: {skill_name}")
        else:
            logger.info(f"Using provided skill name: {skill_name}")

        # Register the skill
        self.skills[skill_name] = skill
        logger.info(f"Registered skill in skills dictionary: {skill_name}")

        # Store the description
        if description:
            self.skill_descriptions[skill_name] = description
            logger.info(f"Using provided description: {description}")
        else:
            # Extract from docstring if available
            doc = inspect.getdoc(skill)
            if doc:
                # Use the first line of the docstring
                self.skill_descriptions[skill_name] = doc.split("\n")[0]
                logger.info(
                    f"Using docstring description: {self.skill_descriptions[skill_name]}"
                )
            else:
                self.skill_descriptions[skill_name] = f"{skill_name} skill"
                logger.info(
                    f"Using default description: {self.skill_descriptions[skill_name]}"
                )

        # Store function descriptions
        self.function_descriptions[skill_name] = {}
        for name, method in inspect.getmembers(skill, inspect.ismethod):
            # Skip private methods
            if name.startswith("_"):
                continue

            # Check if it's a kernel function
            if hasattr(method, "kernel_function"):
                # Get the description from the kernel_function attribute
                desc = getattr(method.kernel_function, "description", "")
                if desc:
                    self.function_descriptions[skill_name][name] = desc
                else:
                    # Extract from docstring if available
                    doc = inspect.getdoc(method)
                    if doc:
                        # Use the first line of the docstring
                        self.function_descriptions[skill_name][name] = doc.split("\n")[
                            0
                        ]
                    else:
                        self.function_descriptions[skill_name][
                            name
                        ] = f"{name} function"
            # Also check for methods with a kernel_function attribute directly
            elif hasattr(skill, name) and hasattr(
                getattr(skill, name), "kernel_function"
            ):
                method = getattr(skill, name)
                desc = getattr(method.kernel_function, "description", "")
                if desc:
                    self.function_descriptions[skill_name][name] = desc
                else:
                    # Extract from docstring if available
                    doc = inspect.getdoc(method)
                    if doc:
                        # Use the first line of the docstring
                        self.function_descriptions[skill_name][name] = doc.split("\n")[
                            0
                        ]
                    else:
                        self.function_descriptions[skill_name][
                            name
                        ] = f"{name} function"

        # Store keywords
        if keywords:
            self.keywords[skill_name] = set(keywords)
            logger.info(f"Using provided keywords: {keywords}")
        else:
            # Check for default keywords first
            if skill.__class__.__name__ in DEFAULT_SKILL_KEYWORDS:
                self.keywords[skill_name] = set(
                    DEFAULT_SKILL_KEYWORDS[skill.__class__.__name__]
                )
                logger.info(
                    f"Using default keywords for {skill.__class__.__name__}: {self.keywords[skill_name]}"
                )
            else:
                # Extract keywords from skill name and description
                self.keywords[skill_name] = set()
                logger.info("Extracting keywords from skill name and description")

                if skill_name:
                    name_keywords = skill_name.lower().split("_")
                    self.keywords[skill_name].update(name_keywords)
                    logger.info(f"Added keywords from skill name: {name_keywords}")

                if skill_name in self.skill_descriptions:
                    desc_keywords = self.skill_descriptions[skill_name].lower().split()
                    self.keywords[skill_name].update(desc_keywords)
                    logger.info(f"Added keywords from description: {desc_keywords}")

        logger.info(f"Final keywords for {skill_name}: {self.keywords[skill_name]}")
        logger.info(
            f"Registered skill: {skill_name} with {len(self.function_descriptions[skill_name])} functions"
        )

        # Log all registered skills for debugging
        logger.info(f"All registered skills: {list(self.skills.keys())}")
        logger.info(f"All keywords: {self.keywords}")

        return skill_name

    def get_skill(self, skill_name: str) -> Optional[Any]:
        """
        Get a skill by name.

        Args:
            skill_name: The name of the skill to retrieve

        Returns:
            The skill instance, or None if not found
        """
        return self.skills.get(skill_name)

    def get_all_skills(self) -> Dict[str, Any]:
        """
        Get all registered skills.

        Returns:
            Dictionary of skill names to skill instances
        """
        return self.skills

    def get_skill_description(self, skill_name: str) -> Optional[str]:
        """
        Get the description of a skill.

        Args:
            skill_name: The name of the skill

        Returns:
            The skill description, or None if not found
        """
        return self.skill_descriptions.get(skill_name)

    def get_function_descriptions(self, skill_name: str) -> Dict[str, str]:
        """
        Get descriptions of all functions in a skill.

        Args:
            skill_name: The name of the skill

        Returns:
            Dictionary of function names to descriptions
        """
        return self.function_descriptions.get(skill_name, {})

    def find_skills_by_keywords(self, query: str) -> List[str]:
        """
        Find skills matching the given keywords.

        Args:
            query: The search query

        Returns:
            List of matching skill names, sorted by relevance
        """
        logger.info(f"Finding skills for query: '{query}'")
        query_words = set(query.lower().split())
        logger.info(f"Query words: {query_words}")
        matches = []

        logger.info(f"Available keywords: {self.keywords}")
        for skill_name, keywords in self.keywords.items():
            # Calculate match score based on keyword overlap
            overlap = query_words.intersection(keywords)
            logger.info(
                f"Skill: {skill_name}, Keywords: {keywords}, Overlap: {overlap}"
            )
            if overlap:
                matches.append((skill_name, len(overlap)))
                logger.info(f"Added match: {skill_name} with score {len(overlap)}")

        # Sort by match score (descending)
        matches.sort(key=lambda x: x[1], reverse=True)
        logger.info(f"Sorted matches: {matches}")

        result = [skill_name for skill_name, _ in matches]
        logger.info(f"Returning matches: {result}")
        return result

    def find_skill_for_request(self, request: str) -> Optional[str]:
        """
        Find the most appropriate skill for a given request.

        Args:
            request: The user request

        Returns:
            The name of the most appropriate skill, or None if no match
        """
        logger.info(f"Finding skill for request: '{request}'")
        matches = self.find_skills_by_keywords(request)
        logger.info(f"Matches found: {matches}")

        result = matches[0] if matches else None
        logger.info(f"Selected skill: {result}")

        # If no skill was found, log a warning
        if result is None:
            logger.warning(f"No skill found for request: '{request}'")

        return result
