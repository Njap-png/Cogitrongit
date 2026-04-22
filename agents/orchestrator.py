"""Orchestrator - Routes tasks to correct agents."""

import logging
from typing import Optional, Dict, Any, List

from core.config import Config
from core.llm import LLMBackend
from core.memory import ConversationMemory
from core.thinking import ThinkingController

from agents.base_agent import BaseAgent
from agents.web_agent import WebAgent
from agents.decoder_agent import DecoderAgent
from agents.analyzer_agent import AnalyzerAgent
from agents.report_agent import ReportAgent
from agents.educator_agent import EducatorAgent

logger = logging.getLogger("phantom.orchestrator")


class Orchestrator:
    """Routes tasks to correct agents."""

    TASK_PATTERNS = {
        "web": [
            r"(?i)^(search|find|google|lookup)",
            r"(?i)https?://",
            r"(?i)visit|crawl|browse",
        ],
        "decode": [
            r"(?i)^(decode|decrypt|uncode)",
            r"(?i)^base64|base32|hex|rot13",
            r"(?i)encode|encrypt|crypt",
        ],
        "analyze": [
            r"(?i)analyz|review|audit",
            r"(?i)vuln|exploit|security",
            r"(?i)code.*audit|scan",
        ],
        "report": [
            r"(?i)^report|document",
            r"(?i)cve-|bug.*bounty",
            r"(?i)vuln.*assess",
        ],
        "educate": [
            r"(?i)^teach|learn|explain",
            r"(?i)^ctf|challenge",
            r"(?i)^quiz|course",
        ],
    }

    def __init__(
        self,
        config: Optional[Config] = None,
        llm: Optional[LLMBackend] = None,
        memory: Optional[ConversationMemory] = None,
        thinking: Optional[ThinkingController] = None
    ):
        """Initialize orchestrator."""
        self.config = config or Config.get_instance()
        self.llm = llm or LLMBackend(self.config)
        self.memory = memory or ConversationMemory(self.config)
        self.thinking = thinking or ThinkingController(self.llm)

        self.agents: Dict[str, BaseAgent] = {}
        self._init_agents()

    def _init_agents(self) -> None:
        """Initialize all agents."""
        self.agents = {
            "web": WebAgent(
                config=self.config,
                llm=self.llm,
                memory=self.memory,
                thinking=self.thinking,
            ),
            "decode": DecoderAgent(
                config=self.config,
                llm=self.llm,
                memory=self.memory,
                thinking=self.thinking,
            ),
            "analyze": AnalyzerAgent(
                config=self.config,
                llm=self.llm,
                memory=self.memory,
                thinking=self.thinking,
            ),
            "report": ReportAgent(
                config=self.config,
                llm=self.llm,
                memory=self.memory,
                thinking=self.thinking,
            ),
            "educate": EducatorAgent(
                config=self.config,
                llm=self.llm,
                memory=self.memory,
                thinking=self.thinking,
            ),
        }

        logger.info(f"Initialized {len(self.agents)} agents")

    def route_task(self, task: str) -> str:
        """Determine which agent to use."""
        import re

        for agent_name, patterns in self.TASK_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, task):
                    return agent_name

        return "educate"

    async def execute(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Execute task with appropriate agent."""
        agent_name = self.route_task(task)
        agent = self.agents.get(agent_name)

        if not agent:
            return "No suitable agent found."

        try:
            logger.info(f"Routing task to {agent_name} agent")
            result = await agent.run(task, context)
            return result

        except Exception as e:
            logger.error(f"Agent execution failed: {e}")
            return f"Error: {e}"

    def list_agents(self) -> List[Dict[str, Any]]:
        """List all agents and their status."""
        return [agent.get_info() for agent in self.agents.values()]

    def get_agent(self, name: str) -> Optional[BaseAgent]:
        """Get specific agent."""
        return self.agents.get(name.lower())

    def activate_agent(self, name: str) -> bool:
        """Activate an agent."""
        agent = self.agents.get(name.lower())
        if agent:
            agent.activate()
            return True
        return False

    def deactivate_agent(self, name: str) -> bool:
        """Deactivate an agent."""
        agent = self.agents.get(name.lower())
        if agent:
            agent.deactivate()
            return True
        return False