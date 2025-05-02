"""
Core RAG prompt templates and utilities for Konveyor.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional  # noqa: F401, F401


@dataclass
class PromptTemplate:
    """Base class for RAG prompt templates."""

    system_message: str
    user_message: str

    def format(self, **kwargs) -> Dict[str, str]:
        """Format the prompt template with given parameters."""
        return {
            "system": self.system_message.format(**kwargs),
            "user": self.user_message.format(**kwargs),
        }


# Default prompt templates
KNOWLEDGE_QUERY_TEMPLATE = PromptTemplate(
    system_message="""You are a knowledgeable assistant that helps answer questions based on the provided context.   # noqa: E501, W291
    Always cite your sources and be direct in your responses.""",
    user_message="""Context: {context}
      # noqa: W293
    Question: {query}
      # noqa: W293
    Please provide a clear and concise answer based on the context above. If you cannot find the answer in the context,   # noqa: E501
    say so explicitly.""",
)

CODE_QUERY_TEMPLATE = PromptTemplate(
    system_message="""You are a technical assistant that helps explain code and development concepts based on the provided context.  # noqa: E501
    Always reference specific code examples when available.""",
    user_message="""Code Context: {context}
      # noqa: W293
    Question: {query}
      # noqa: W293
    Please explain the relevant code aspects from the context above. If the context doesn't contain relevant information,  # noqa: E501
    state that explicitly.""",
)


class RAGPromptManager:
    """Manages prompt templates for different RAG scenarios."""

    def __init__(self):
        self.templates = {
            "knowledge": KNOWLEDGE_QUERY_TEMPLATE,
            "code": CODE_QUERY_TEMPLATE,
        }

    def get_template(self, template_type: str) -> PromptTemplate:
        """Get a prompt template by type."""
        if template_type not in self.templates:
            raise ValueError(f"Unknown template type: {template_type}")
        return self.templates[template_type]

    def add_template(self, name: str, template: PromptTemplate):
        """Add a new prompt template."""
        self.templates[name] = template

    def format_prompt(self, template_type: str, **kwargs) -> Dict[str, str]:
        """Format a prompt template with given parameters."""
        template = self.get_template(template_type)
        return template.format(**kwargs)
