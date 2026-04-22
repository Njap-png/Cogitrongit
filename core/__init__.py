"""PHANTOM - Polymorphic Heuristic AI for Network Threat Analysis & Mentoring"""

__version__ = "2.0.3-OMEGA"
__codename__ = "OMEGA-CORE"
__author__ = "PHANTOM-CORE PROJECT"
__license__ = "MIT"
__tagline__ = "What you can't see can still compromise you."

from core.config import Config
from core.llm import LLMBackend
from core.thinking import ThinkingController, ThinkingResult
from core.memory import ConversationMemory
from core.evolution import EvolutionEngine
from core.soul import Soul, PersonalityCore, Emotion, Manner
from core.learner import Learner, SelfLearning, LearnedConcept
from core.cli import CLI, CommandRunner, FileEditor, CommandResult
from core.updater import SelfUpdater, CodeEditor, VersionManager, UpdateResult
from core.video_learner import VideoLearner, VideoInfo, MediaSearchResult
from core.youtube import YouTubeExtractor, YouTubeVideo, VideoLearning, VideoSearchResult as YouTubeSearchResult
from core.sandbox import Sandbox, ExecutionResult, SandboxConfig, temporary_sandbox, quick_execute
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
    "Soul",
    "PersonalityCore",
    "Emotion",
    "Manner",
    "Learner",
    "SelfLearning",
    "LearnedConcept",
    "CLI",
    "CommandRunner",
    "FileEditor",
    "CommandResult",
    "SelfUpdater",
    "CodeEditor",
    "VersionManager",
    "UpdateResult",
    "VideoLearner",
    "VideoInfo",
    "MediaSearchResult",
    "YouTubeExtractor",
    "YouTubeVideo",
    "VideoLearning",
    "YouTubeSearchResult",
    "Sandbox",
    "ExecutionResult",
    "SandboxConfig",
    "temporary_sandbox",
    "quick_execute",
    "KnowledgeBase",
    "Decoder",
    "WebSearch",
    "WebCrawler",
    "WebViewer",
]