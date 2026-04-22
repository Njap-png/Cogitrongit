"""PHANTOM - Polymorphic Heuristic AI for Network Threat Analysis & Mentoring"""

__version__ = "2.0.0-OMEGA"
__codename__ = "OMEGA-CORE"
__author__ = "PHANTOM-CORE PROJECT"
__license__ = "MIT"
__tagline__ = "What you can't see can still compromise you."

from core.config import Config
from core.llm import LLMBackend
from core.thinking import ThinkingController, ThinkingResult
from core.memory import ConversationMemory
from core.evolution import EvolutionEngine
from tools.knowledge_base import KnowledgeBase
from tools.decoder import Decoder
from tools.web_search import WebSearch
from tools.web_crawler import WebCrawler
from tools.web_viewer import WebViewer

__all__ = [
    "Config",
    "LLMBackend", 
    "ThinkingController",
    "ThinkingResult",
    "ConversationMemory",
    "EvolutionEngine",
    "KnowledgeBase",
    "Decoder",
    "WebSearch",
    "WebCrawler",
    "WebViewer",
]