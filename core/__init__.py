"""PHANTOM - Polymorphic Heuristic AI for Network Threat Analysis & Mentoring

PHANTOM is a Language Learning Model (LLM) with autonomous capabilities:
- Five Thinking Engines for deep reasoning
- Self-learning and memory system
- Soul/personality for authentic interaction
- Autonomous agents for task completion
- Code generation and execution
- YouTube video learning
- Self-update capabilities
"""

__version__ = "2.0.5-OMEGA"
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
from core.agents import AgentOrchestrator, AutonomousAgent, CodeGenerator, ResearchAgent, Task, AgentResponse
from core.language import LanguageLearner, LanguageTutor, VocabularyManager, Word
from tools.knowledge_base import KnowledgeBase
from tools.decoder import Decoder
from tools.web_search import WebSearch
from tools.web_crawler import WebCrawler
from tools.web_viewer import WebViewer

__all__ = [
    # Version
    "__version__",
    "__codename__",
    
    # Core
    "Config",
    "LLMBackend", 
    "ThinkingController",
    "ThinkingResult",
    "ConversationMemory",
    "EvolutionEngine",
    
    # Soul & Personality
    "Soul",
    "PersonalityCore",
    "Emotion",
    "Manner",
    
    # Learning
    "Learner",
    "SelfLearning",
    "LearnedConcept",
    
    # CLI & Execution
    "CLI",
    "CommandRunner",
    "FileEditor",
    "CommandResult",
    
    # Self-Update
    "SelfUpdater",
    "CodeEditor",
    "VersionManager",
    "UpdateResult",
    
    # Video Learning
    "VideoLearner",
    "VideoInfo",
    "MediaSearchResult",
    "YouTubeExtractor",
    "YouTubeVideo",
    "VideoLearning",
    "YouTubeSearchResult",
    
    # Sandbox
    "Sandbox",
    "ExecutionResult",
    "SandboxConfig",
    "temporary_sandbox",
    "quick_execute",
    
    # Autonomous Agents
    "AgentOrchestrator",
    "AutonomousAgent",
    "CodeGenerator",
    "ResearchAgent",
    "Task",
    "AgentResponse",
    
    # Language Learning
    "LanguageLearner",
    "LanguageTutor",
    "VocabularyManager",
    "Word",
    
    # Tools
    "KnowledgeBase",
    "Decoder",
    "WebSearch",
    "WebCrawler",
    "WebViewer",
]