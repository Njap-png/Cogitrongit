"""Configuration manager for PHANTOM."""

import os
import sys
import yaml
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.handlers.RotatingFileHandler(
            Path.home() / ".phantom" / "logs" / "phantom.log",
            maxBytes=10_485_760,
            backupCount=5,
        ),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("phantom.config")


@dataclass
class LLMConfig:
    """LLM configuration settings."""
    backend: str = "auto"
    model: str = ""
    api_key: str = ""
    api_base: str = ""
    max_tokens: int = 2048
    temperature: float = 0.7
    stream: bool = True
    timeout: int = 120


@dataclass
class ThinkingConfig:
    """Thinking engine configuration."""
    default_mode: str = "deep"
    show_engine_outputs: bool = False
    parallel_timeout: int = 30
    chain_temperature: float = 0.3
    synthesis_temperature: float = 0.5


@dataclass
class WebConfig:
    """Web tools configuration."""
    search_engine: str = "duckduckgo"
    searxng_url: str = ""
    google_cse_key: str = ""
    google_cse_id: str = ""
    shodan_api_key: str = ""
    github_token: str = ""
    cache_enabled: bool = True
    cache_ttl_hours: int = 24
    timeout: int = 30
    rate_limit_delay: float = 1.5
    max_concurrent_requests: int = 5
    respect_robots_txt: bool = True
    user_agent: str = "PHANTOM/2.0 Educational Research Tool"


@dataclass
class EvolutionConfig:
    """Self-evolution configuration."""
    auto_learn: bool = True
    evolve_on_startup: bool = False
    max_kb_entries: int = 50000
    passive_extraction: bool = True


@dataclass
class UIConfig:
    """UI configuration."""
    theme: str = "matrix"
    show_token_count: bool = True
    show_thinking_time: bool = True
    show_confidence: bool = True
    pager: bool = True
    history_file: str = "~/.phantom/history"


@dataclass
class PlatformConfig:
    """Platform-specific configuration."""
    termux_mode: bool = False
    minimal_mode: bool = False
    disable_playwright: bool = False


@dataclass
class Config:
    """Main configuration class for PHANTOM."""
    llm: LLMConfig = field(default_factory=LLMConfig)
    thinking: ThinkingConfig = field(default_factory=ThinkingConfig)
    web: WebConfig = field(default_factory=WebConfig)
    evolution: EvolutionConfig = field(default_factory=EvolutionConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    platform: PlatformConfig = field(default_factory=PlatformConfig)
    config_dir: Path = field(default_factory=lambda: Path.home() / ".phantom")
    _instance: Optional["Config"] = field(default=None, repr=False)

    @classmethod
    def get_instance(cls) -> "Config":
        """Get singleton instance of Config."""
        if cls._instance is None:
            cls._instance = cls.load()
        return cls._instance

    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> "Config":
        """Load configuration from YAML file."""
        config_dir = Path.home() / ".phantom"
        config_dir.mkdir(parents=True, exist_ok=True)
        
        if config_path is None:
            config_path = config_dir / "config.yaml"
        
        config = cls()
        config.config_dir = config_dir
        
        if config_path.exists():
            try:
                with open(config_path) as f:
                    data = yaml.safe_load(f) or {}
                
                if "llm" in data:
                    config.llm = LLMConfig(**data["llm"])
                if "thinking" in data:
                    config.thinking = ThinkingConfig(**data["thinking"])
                if "web" in data:
                    config.web = WebConfig(**data["web"])
                if "evolution" in data:
                    config.evolution = EvolutionConfig(**data["evolution"])
                if "ui" in data:
                    config.ui = UIConfig(**data["ui"])
                if "platform" in data:
                    config.platform = PlatformConfig(**data["platform"])
                
                logger.info(f"Loaded config from {config_path}")
            except Exception as e:
                logger.error(f"Failed to load config: {e}")
        
        config._apply_env_overrides()
        config._detect_platform()
        
        return config

    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides."""
        if os.getenv("OPENAI_API_KEY"):
            self.llm.api_key = os.getenv("OPENAI_API_KEY")
        if os.getenv("ANTHROPIC_API_KEY"):
            self.llm.api_key = os.getenv("ANTHROPIC_API_KEY")
        if os.getenv("GROQ_API_KEY"):
            self.llm.api_key = os.getenv("GROQ_API_KEY")
        if os.getenv("OPENROUTER_API_KEY"):
            self.llm.api_key = os.getenv("OPENROUTER_API_KEY")
        if os.getenv("GOOGLE_API_KEY"):
            self.llm.api_key = os.getenv("GOOGLE_API_KEY")
        if os.getenv("SHODAN_API_KEY"):
            self.web.shodan_api_key = os.getenv("SHODAN_API_KEY")
        if os.getenv("GITHUB_TOKEN"):
            self.web.github_token = os.getenv("GITHUB_TOKEN")
        if os.getenv("PHANTOM_THEME"):
            self.ui.theme = os.getenv("PHANTOM_THEME")

    def _detect_platform(self) -> None:
        """Detect current platform."""
        if Path("/data/data/com.termux").exists():
            self.platform.termux_mode = True
            self.platform.minimal_mode = True
            self.platform.disable_playwright = True
            logger.info("Detected Termux platform")
            return
        
        if sys.platform == "win32":
            logger.info("Detected Windows platform")
            return
        
        if sys.platform == "darwin":
            logger.info("Detected macOS platform")
            return
        
        try:
            os_release = Path("/etc/os-release")
            if os_release.exists():
                content = os_release.read_text().lower()
                if "kali" in content:
                    logger.info("Detected Kali platform")
                elif "parrot" in content:
                    logger.info("Detected Parrot platform")
                elif "blackarch" in content:
                    logger.info("Detected BlackArch platform")
        except Exception:
            pass
        
        logger.info("Detected Linux platform")

    def save(self, config_path: Optional[Path] = None) -> None:
        """Save configuration to YAML file."""
        if config_path is None:
            config_path = self.config_dir / "config.yaml"
        
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        data = {
            "llm": {
                "backend": self.llm.backend,
                "model": self.llm.model,
                "api_key": self.llm.api_key,
                "api_base": self.llm.api_base,
                "max_tokens": self.llm.max_tokens,
                "temperature": self.llm.temperature,
                "stream": self.llm.stream,
            },
            "thinking": {
                "default_mode": self.thinking.default_mode,
                "show_engine_outputs": self.thinking.show_engine_outputs,
                "parallel_timeout": self.thinking.parallel_timeout,
                "chain_temperature": self.thinking.chain_temperature,
                "synthesis_temperature": self.thinking.synthesis_temperature,
            },
            "web": {
                "search_engine": self.web.search_engine,
                "searxng_url": self.web.searxng_url,
                "google_cse_key": self.web.google_cse_key,
                "google_cse_id": self.web.google_cse_id,
                "shodan_api_key": self.web.shodan_api_key,
                "github_token": self.web.github_token,
                "cache_enabled": self.web.cache_enabled,
                "cache_ttl_hours": self.web.cache_ttl_hours,
                "timeout": self.web.timeout,
                "rate_limit_delay": self.web.rate_limit_delay,
                "max_concurrent_requests": self.web.max_concurrent_requests,
                "respect_robots_txt": self.web.respect_robots_txt,
                "user_agent": self.web.user_agent,
            },
            "evolution": {
                "auto_learn": self.evolution.auto_learn,
                "evolve_on_startup": self.evolution.evolve_on_startup,
                "max_kb_entries": self.evolution.max_kb_entries,
                "passive_extraction": self.evolution.passive_extraction,
            },
            "ui": {
                "theme": self.ui.theme,
                "show_token_count": self.ui.show_token_count,
                "show_thinking_time": self.ui.show_thinking_time,
                "show_confidence": self.ui.show_confidence,
                "pager": self.ui.pager,
                "history_file": self.ui.history_file,
            },
            "platform": {
                "termux_mode": self.platform.termux_mode,
                "minimal_mode": self.platform.minimal_mode,
                "disable_playwright": self.platform.disable_playwright,
            },
        }
        
        with open(config_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
        
        try:
            os.chmod(config_path, 0o600)
        except Exception:
            pass
        
        logger.info(f"Saved config to {config_path}")

    def get_data_dir(self) -> Path:
        """Get PHANTOM data directory."""
        data_dir = self.config_dir / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir


def detect_platform() -> str:
    """Standalone platform detection function."""
    if Path("/data/data/com.termux").exists():
        return "termux"
    if sys.platform == "win32":
        return "windows"
    if sys.platform == "darwin":
        return "macos"
    
    try:
        os_release = Path("/etc/os-release")
        if os_release.exists():
            content = os_release.read_text().lower()
            if "kali" in content:
                return "kali"
            if "parrot" in content:
                return "parrot"
            if "blackarch" in content:
                return "blackarch"
    except Exception:
        pass
    
    return "linux"