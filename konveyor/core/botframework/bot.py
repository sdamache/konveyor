import asyncio  # noqa: F401
import logging
import traceback
from typing import Any, Dict, Optional  # noqa: F401

from botbuilder.core import ActivityHandler, TurnContext
from botbuilder.schema import Activity, ActivityTypes

from konveyor.core.agent import AgentOrchestratorSkill, SkillRegistry
from konveyor.core.chat import ChatSkill
from konveyor.core.kernel import create_kernel

logger = logging.getLogger(__name__)


class KonveyorBot(ActivityHandler):
    """
    Bot implementation for Konveyor.

    This bot handles incoming messages from users, routes them to the appropriate
    skills via the Agent Orchestrator, and returns the responses.
    """

    def __init__(self):
        """Initialize the bot with required components."""
        super().__init__()
        self._initialize_components()

    def _initialize_components(self):
        """Initialize the kernel, skills, and orchestrator."""
        try:
            # Create the kernel with validation disabled for better error handling
            self.kernel = create_kernel(validate=False)
            logger.info("Created Semantic Kernel for bot")

            # Create the skill registry
            self.registry = SkillRegistry()
            logger.info("Created skill registry")

            # Create the orchestrator
            self.orchestrator = AgentOrchestratorSkill(self.kernel, self.registry)
            logger.info("Created Agent Orchestrator")

            # Register the orchestrator with the kernel
            self.kernel.add_plugin(self.orchestrator, plugin_name="orchestrator")
            logger.info("Registered orchestrator with kernel")

            # Register the ChatSkill
            chat_skill = ChatSkill()
            self.orchestrator.register_skill(
                chat_skill,
                "ChatSkill",
                "Handles general chat interactions and questions",
                ["chat", "question", "answer", "help"],
            )
            logger.info("Registered ChatSkill with orchestrator")

            # Initialize conversation state
            self.conversations: Dict[str, Dict[str, Any]] = {}
            logger.info("Initialized conversation state")

        except Exception as e:
            logger.error(f"Error initializing bot components: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    async def on_message_activity(self, turn_context: TurnContext):
        """
        Handle incoming messages from users.

        Args:
            turn_context: The turn context containing the user's message
        """
        try:
            # Get the user's message
            user_message = turn_context.activity.text
            if not user_message:
                return await turn_context.send_activity(
                    Activity(
                        type=ActivityTypes.message,
                        text="I received your message but it was empty. Please try again.",  # noqa: E501
                    )
                )

            # Get or create conversation state
            conversation_id = turn_context.activity.conversation.id
            if conversation_id not in self.conversations:
                self.conversations[conversation_id] = {"history": ""}

            # Get conversation history
            context = {
                "history": self.conversations[conversation_id].get("history", ""),
                "user_id": turn_context.activity.from_property.id,
                "conversation_id": conversation_id,
            }

            # Process the request through the orchestrator
            logger.info(f"Processing message: {user_message[:50]}...")

            # Show typing indicator
            await turn_context.send_activities([Activity(type="typing")])

            # Process the request
            result = await self.orchestrator.process_request(user_message, context)

            # Extract the response
            if isinstance(result, dict) and "response" in result:
                response_text = result["response"]

                # Update conversation history if available
                if "history" in result:
                    self.conversations[conversation_id]["history"] = result["history"]
            else:
                response_text = str(result)

            # Format the response for Slack if needed
            if hasattr(self.orchestrator, "format_for_slack"):
                response_text = await self.orchestrator.format_for_slack(response_text)

            # Send the response
            await turn_context.send_activity(
                Activity(type=ActivityTypes.message, text=response_text)
            )

        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            logger.error(traceback.format_exc())
            await turn_context.send_activity(
                Activity(
                    type=ActivityTypes.message,
                    text=f"I encountered an error while processing your request: {str(e)}",  # noqa: E501
                )
            )

    async def on_members_added_activity(self, members_added, turn_context: TurnContext):
        """
        Handle new members being added to the conversation.

        Args:
            members_added: The list of members added
            turn_context: The turn context
        """
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity(
                    Activity(
                        type=ActivityTypes.message,
                        text="Welcome to Konveyor Bot! I can help you with questions, chat, and more. Type something to get started.",  # noqa: E501
                    )
                )
