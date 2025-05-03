"""
Response generator factory for Konveyor.

This module provides a factory for creating response generators based on the
specified generator type and configuration.
"""

import logging
from typing import Any

from konveyor.core.generation.generator import ResponseGenerator
from konveyor.core.generation.interface import ResponseGeneratorInterface

logger = logging.getLogger(__name__)


class ResponseGeneratorFactory:
    """
    Factory for creating response generators.

    This class provides methods for creating response generators based on the
    specified generator type and configuration. It supports different generator
    types and configurations.
    """

    _generators = {}

    @classmethod
    def get_generator(
        cls, generator_type: str = "default", config: dict[str, Any] | None = None
    ) -> ResponseGeneratorInterface:
        """
        Get a response generator.

        Args:
            generator_type: Type of generator to get ('default', 'rag', 'chat')
            config: Configuration for the generator

        Returns:
            A response generator implementing the ResponseGeneratorInterface

        Raises:
            ValueError: If the generator type is not supported
        """
        # Check if we already have an instance of this generator type
        if generator_type in cls._generators:
            return cls._generators[generator_type]

        # Get configuration
        openai_client_type = (
            config.get("openai_client_type", "unified") if config else "unified"
        )
        openai_config = config.get("openai_config") if config else None
        context_service = config.get("context_service") if config else None
        conversation_service = config.get("conversation_service") if config else None

        # Create a new generator instance
        if generator_type == "default":
            logger.debug("Creating default response generator")
            generator = ResponseGenerator(
                openai_client_type=openai_client_type,
                openai_config=openai_config,
                context_service=context_service,
                conversation_service=conversation_service,
            )
        elif generator_type == "rag":
            logger.debug("Creating RAG response generator")
            # For RAG, we need a context service
            if not context_service:
                logger.warning(
                    "Context service not provided for RAG generator, using default generator"  # noqa: E501
                )
                return cls.get_generator("default", config)

            generator = ResponseGenerator(
                openai_client_type=openai_client_type,
                openai_config=openai_config,
                context_service=context_service,
                conversation_service=conversation_service,
            )
        elif generator_type == "chat":
            logger.debug("Creating chat response generator")
            # For chat, we need a conversation service
            if not conversation_service:
                logger.warning(
                    "Conversation service not provided for chat generator, using default generator"  # noqa: E501
                )
                return cls.get_generator("default", config)

            generator = ResponseGenerator(
                openai_client_type=openai_client_type,
                openai_config=openai_config,
                context_service=context_service,
                conversation_service=conversation_service,
            )
        else:
            logger.error(f"Unsupported generator type: {generator_type}")
            raise ValueError(f"Unsupported generator type: {generator_type}")

        # Cache the generator instance
        cls._generators[generator_type] = generator

        return generator

    @classmethod
    def register_generator(
        cls, generator_type: str, generator: ResponseGeneratorInterface
    ) -> None:
        """
        Register a custom generator.

        Args:
            generator_type: Type of generator to register
            generator: The generator instance

        Raises:
            ValueError: If the generator does not implement ResponseGeneratorInterface
        """
        if not isinstance(generator, ResponseGeneratorInterface):
            raise ValueError("Generator must implement ResponseGeneratorInterface")

        logger.debug(f"Registering custom generator for {generator_type}")
        cls._generators[generator_type] = generator
