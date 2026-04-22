"""Base Agent - Abstract agent with thinking engine access."""

import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List

from core.config import Config
from core.llm import LLMBackend
from core.thinking import ThinkingController, ThinkingResult
from core.memory import ConversationMemory

logger = logging.getLogger("phantom.agents")


class BaseAgent(ABC):
    """Abstract base agent with shared functionality."""

    def __init__(
        self,
        config: Optional[Config] = None,
        llm: Optional[LLMBackend] = None,
        memory: Optional[ConversationMemory] = None,
        thinking: Optional[ThinkingController] = None
    ):
        """Initialize base agent."""
        self.config = config or Config.get_instance()
        self.llm = llm or LLMBackend(self.config)
        self.memory = memory or ConversationMemory(self.config)
        self.thinking = thinking or ThinkingController(self.llm)
        self.name = self.__class__.__name__
        self._active = True

    @abstractmethod
    async def run(self, task: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Run agent task."""
        pass

    async def think(
        self,
        query: str,
        mode: str = "deep"
    ) -> ThinkingResult:
        """Use thinking engines for reasoning."""
        return await self.thinking.think(query, mode=mode)

    def chat(
        self,
        message: str,
        context: Optional[str] = None
    ) -> str:
        """Direct chat with LLM."""
        messages = self.llm.format_messages(message, context)
        result = ""
        for chunk in self.llm.chat(messages, stream=False):
            result += chunk
        return result

    def activate(self) -> None:
        """Activate agent."""
        self._active = True
        logger.info(f"{self.name} activated")

    def deactivate(self) -> None:
        """Deactivate agent."""
        self._active = False
        logger.info(f"{self.name} deactivated")

    def is_active(self) -> bool:
        """Check if agent is active."""
        return self._active

    def get_capabilities(self) -> List[str]:
        """Get agent capabilities."""
        return []

    def get_info(self) -> Dict[str, Any]:
        """Get agent info."""
        return {
            "name": self.name,
            "active": self._active,
            "capabilities": self.get_capabilities(),
        }