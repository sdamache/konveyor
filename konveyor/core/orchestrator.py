from typing import Any, Callable


class RequestParser:
    """Parses incoming requests and determines intent."""
    def parse(self, request: Any) -> str:
        """Extract intent from the request payload."""
        raise NotImplementedError


class SkillRouter:
    """Routes parsed intents to registered skill handlers."""
    def __init__(self):
        self._skills: dict[str, Callable[[Any], Any]] = {}

    def register(self, intent: str, handler: Callable[[Any], Any]) -> None:
        """Register a handler function for a given intent."""
        self._skills[intent] = handler

    async def route(self, intent: str, request: Any) -> Any:
        """Dispatch request to the appropriate skill handler based on intent."""
        handler = self._skills.get(intent)
        if not handler:
            raise ValueError(f"No handler registered for intent: {intent}")
        return await handler(request)


class AgentOrchestrator:
    """High-level orchestrator for handling incoming requests."""
    def __init__(self, parser: RequestParser, router: SkillRouter):
        self._parser = parser
        self._router = router

    async def handle_request(self, request: Any) -> Any:
        """Parse the request and dispatch to the appropriate skill."""
        intent = self._parser.parse(request)
        return await self._router.route(intent, request)
