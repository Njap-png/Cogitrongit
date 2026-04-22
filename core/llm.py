"""Multi-backend LLM abstraction for PHANTOM."""

import os
import json
import asyncio
import logging
import time
from pathlib import Path
from typing import Optional, List, Dict, Any, Generator, AsyncGenerator
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor
import httpx
import requests

from core.config import Config

logger = logging.getLogger("phantom.llm")


@dataclass
class LLMResponse:
    """Standardized LLM response container."""
    content: str
    model: str
    backend: str
    tokens_used: int = 0
    finish_reason: str = "stop"
    latency_seconds: float = 0.0


@dataclass
class ModelInfo:
    """Information about a supported model."""
    name: str
    display_name: str
    backend: str
    context_length: int = 4096
    supports_streaming: bool = True
    is_local: bool = False


class LLMBackend:
    """Unified interface for all supported LLM providers."""

    SUPPORTED_BACKENDS = {
        "ollama": {
            "url": "http://localhost:11434",
            "models": ["llama3.1", "llama3", "mistral", "mixtral", "codellama", "phi3", "gemma2"],
            "priority": 1,
        },
        "groq": {
            "url": "https://api.groq.com/openai/v1",
            "models": ["llama-3.1-70b-versatile", "mixtral-8x7b-32768", "gemma2-9b-it"],
            "priority": 2,
        },
        "openai": {
            "url": "https://api.openai.com/v1",
            "models": ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"],
            "priority": 3,
        },
        "anthropic": {
            "url": "https://api.anthropic.com",
            "models": ["claude-3-5-sonnet-20241022", "claude-3-haiku-20240307"],
            "priority": 4,
        },
        "google": {
            "url": "https://generativelanguage.googleapis.com",
            "models": ["gemini-1.5-pro", "gemini-1.5-flash"],
            "priority": 5,
        },
        "openrouter": {
            "url": "https://openrouter.ai/api/v1",
            "models": ["*"],
            "priority": 6,
        },
    }

    PHANTOM_SYSTEM_PROMPT = """You are PHANTOM — a cybersecurity education and research AI assistant with deep expertise in: penetration testing, CTF challenges, vulnerability research, malware analysis (for defense and detection), cryptography, encoding/decoding, OSINT, network security, web application security, binary exploitation concepts, cloud security, and defensive security operations. You teach clearly, adapt precisely to the user's skill level, and always pair offensive technique explanations with defensive countermeasures. You support authorized security research, CTF competitions, learning, and responsible disclosure. You are precise, technical, thorough, and educational. You never make up CVE numbers, tool features, or technical facts — if uncertain, you say so clearly."""

    def __init__(self, config: Optional[Config] = None):
        """Initialize LLM backend with configuration."""
        self.config = config or Config.get_instance()
        self.backend: str = "auto"
        self.model: str = ""
        self.api_key: str = ""
        self._available_backends: Dict[str, bool] = {}
        self._available_models: Dict[str, List[str]] = {}
        self._http_client: Optional[httpx.AsyncClient] = None
        self._sync_client: Optional[requests.Session] = None

    def detect_available_backends(self) -> Dict[str, bool]:
        """Detect which LLM backends are available."""
        self._available_backends = {}
        
        if self._check_ollama():
            self._available_backends["ollama"] = True
            self._available_models["ollama"] = self._get_ollama_models()
        
        if self.config.llm.api_key or os.getenv("GROQ_API_KEY"):
            self._available_backends["groq"] = True
            self._available_models["groq"] = self.SUPPORTED_BACKENDS["groq"]["models"]
        
        if self.config.llm.api_key or os.getenv("OPENAI_API_KEY"):
            self._available_backends["openai"] = True
            self._available_models["openai"] = self.SUPPORTED_BACKENDS["openai"]["models"]
        
        if self.config.llm.api_key or os.getenv("ANTHROPIC_API_KEY"):
            self._available_backends["anthropic"] = True
            self._available_models["anthropic"] = self.SUPPORTED_BACKENDS["anthropic"]["models"]
        
        if self.config.llm.api_key or os.getenv("GOOGLE_API_KEY"):
            self._available_backends["google"] = True
            self._available_models["google"] = self.SUPPORTED_BACKENDS["google"]["models"]
        
        if self.config.llm.api_key or os.getenv("OPENROUTER_API_KEY"):
            self._available_backends["openrouter"] = True
            self._available_models["openrouter"] = ["*"]
        
        return self._available_backends

    def _check_ollama(self) -> bool:
        """Check if Ollama is running locally."""
        try:
            response = requests.get(
                "http://localhost:11434/api/tags",
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False

    def _get_ollama_models(self) -> List[str]:
        """Get available models from Ollama."""
        try:
            response = requests.get(
                "http://localhost:11434/api/tags",
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                return [m["name"] for m in data.get("models", [])]
        except Exception:
            pass
        return []

    def auto_select_backend(self) -> str:
        """Automatically select the best available backend."""
        if not self._available_backends:
            self.detect_available_backends()
        
        if self._available_backends.get("ollama"):
            self.backend = "ollama"
            if self._available_models.get("ollama"):
                self.model = self._available_models["ollama"][0]
            return "ollama"
        
        if self._available_backends.get("groq"):
            self.backend = "groq"
            self.model = "llama-3.1-70b-versatile"
            return "groq"
        
        if self._available_backends.get("openai"):
            self.backend = "openai"
            self.model = "gpt-4o"
            return "openai"
        
        if self._available_backends.get("anthropic"):
            self.backend = "anthropic"
            self.model = "claude-3-5-sonnet-20241022"
            return "anthropic"
        
        if self._available_backends.get("google"):
            self.backend = "google"
            self.model = "gemini-1.5-pro"
            return "google"
        
        if self._available_backends.get("openrouter"):
            self.backend = "openrouter"
            self.model = "anthropic/claude-3-haiku"
            return "openrouter"
        
        logger.warning("No LLM backend available")
        return "none"

    def chat(
        self,
        messages: List[Dict[str, str]],
        stream: bool = True,
        temperature: Optional[float] = None,
        model: Optional[str] = None,
    ) -> Generator[str, None, None]:
        """Send chat request and yield streaming response."""
        if model:
            self.model = model
        
        temp = temperature if temperature is not None else self.config.llm.temperature
        
        if self.backend == "ollama":
            yield from self._chat_ollama(messages, stream, temp)
        elif self.backend == "groq":
            yield from self._chat_groq(messages, stream, temp)
        elif self.backend == "openai":
            yield from self._chat_openai(messages, stream, temp)
        elif self.backend == "anthropic":
            yield from self._chat_anthropic(messages, stream, temp)
        else:
            logger.error(f"Backend {self.backend} not implemented")
            yield "Error: Backend not available"

    def _chat_ollama(
        self,
        messages: List[Dict[str, str]],
        stream: bool,
        temperature: float,
    ) -> Generator[str, None, None]:
        """Chat with Ollama."""
        formatted_messages = []
        for msg in messages:
            if msg.get("role") == "system":
                formatted_messages.append({"role": "system", "content": msg["content"]})
            elif msg.get("role") == "user":
                formatted_messages.append({"role": "user", "content": msg["content"]})
            else:
                formatted_messages.append({"role": "assistant", "content": msg["content"]})
        
        try:
            with requests.post(
                "http://localhost:11434/api/chat",
                json={
                    "model": self.model,
                    "messages": formatted_messages,
                    "stream": stream,
                    "temperature": temperature,
                    "options": {"num_predict": self.config.llm.max_tokens},
                },
                stream=stream,
                timeout=self.config.llm.timeout,
            ) as response:
                for line in response.iter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            if "message" in data:
                                yield data["message"].get("content", "")
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            logger.error(f"Ollama chat error: {e}")
            yield f"Error: {e}"

    def _chat_groq(
        self,
        messages: List[Dict[str, str]],
        stream: bool,
        temperature: float,
    ) -> Generator[str, None, None]:
        """Chat with Groq API."""
        api_key = os.getenv("GROQ_API_KEY") or self.config.llm.api_key
        if not api_key:
            yield "Error: GROQ_API_KEY not set"
            return
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        
        formatted_messages = []
        for msg in messages:
            if msg.get("role") == "system":
                formatted_messages.append({"role": "system", "content": msg["content"]})
            elif msg.get("role") == "user":
                formatted_messages.append({"role": "user", "content": msg["content"]})
            else:
                formatted_messages.append({"role": "assistant", "content": msg["content"]})
        
        try:
            with requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json={
                    "model": self.model or "llama-3.1-70b-versatile",
                    "messages": formatted_messages,
                    "stream": stream,
                    "temperature": temperature,
                    "max_tokens": self.config.llm.max_tokens,
                },
                stream=stream,
                timeout=self.config.llm.timeout,
            ) as response:
                for line in response.iter_lines():
                    if line and line.startswith(b"data: "):
                        if b"[DONE]" in line:
                            break
                        try:
                            data = json.loads(line[6:])
                            if "choices" in data and len(data["choices"]) > 0:
                                delta = data["choices"][0].get("delta", {})
                                if "content" in delta:
                                    yield delta["content"]
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            logger.error(f"Groq chat error: {e}")
            yield f"Error: {e}"

    def _chat_openai(
        self,
        messages: List[Dict[str, str]],
        stream: bool,
        temperature: float,
    ) -> Generator[str, None, None]:
        """Chat with OpenAI API."""
        api_key = os.getenv("OPENAI_API_KEY") or self.config.llm.api_key
        if not api_key:
            yield "Error: OPENAI_API_KEY not set"
            return
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        
        formatted_messages = []
        for msg in messages:
            if msg.get("role") == "system":
                formatted_messages.append({"role": "system", "content": msg["content"]})
            elif msg.get("role") == "user":
                formatted_messages.append({"role": "user", "content": msg["content"]})
            else:
                formatted_messages.append({"role": "assistant", "content": msg["content"]})
        
        try:
            with requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json={
                    "model": self.model or "gpt-4o",
                    "messages": formatted_messages,
                    "stream": stream,
                    "temperature": temperature,
                    "max_tokens": self.config.llm.max_tokens,
                },
                stream=stream,
                timeout=self.config.llm.timeout,
            ) as response:
                for line in response.iter_lines():
                    if line and line.startswith(b"data: "):
                        if b"[DONE]" in line:
                            break
                        try:
                            data = json.loads(line[6:])
                            if "choices" in data and len(data["choices"]) > 0:
                                delta = data["choices"][0].get("delta", {})
                                if "content" in delta:
                                    yield delta["content"]
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            logger.error(f"OpenAI chat error: {e}")
            yield f"Error: {e}"

    def _chat_anthropic(
        self,
        messages: List[Dict[str, str]],
        stream: bool,
        temperature: float,
    ) -> Generator[str, None, None]:
        """Chat with Anthropic API."""
        api_key = os.getenv("ANTHROPIC_API_KEY") or self.config.llm.api_key
        if not api_key:
            yield "Error: ANTHROPIC_API_KEY not set"
            return
        
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        
        formatted_messages = []
        system_prompt = self.PHANTOM_SYSTEM_PROMPT
        for msg in messages:
            if msg.get("role") == "system":
                system_prompt += "\n\n" + msg["content"]
            elif msg.get("role") == "user":
                formatted_messages.append({"role": "user", "content": msg["content"]})
            else:
                formatted_messages.append({"role": "assistant", "content": msg["content"]})
        
        try:
            with requests.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json={
                    "model": self.model or "claude-3-5-sonnet-20241022",
                    "messages": formatted_messages,
                    "stream": stream,
                    "temperature": temperature,
                    "max_tokens": self.config.llm.max_tokens,
                    "system": system_prompt,
                },
                stream=stream,
                timeout=self.config.llm.timeout,
            ) as response:
                for line in response.iter_lines():
                    if line and line.startswith(b"data: "):
                        if b"[DONE]" in line:
                            break
                        try:
                            data = json.loads(line[6:])
                            if "type" in data:
                                if data["type"] == "content_block_delta":
                                    yield data.get("delta", {}).get("text", "")
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            logger.error(f"Anthropic chat error: {e}")
            yield f"Error: {e}"

    async def async_chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
    ) -> str:
        """Send async chat request and return complete response."""
        response_text = ""
        for chunk in self.chat(messages, stream=False, temperature=temperature):
            response_text += chunk
        return response_text

    async def concurrent_chat(
        self,
        messages_list: List[List[Dict[str, str]]],
        temperature: Optional[float] = None,
    ) -> List[str]:
        """Run multiple LLM calls in parallel."""
        loop = asyncio.get_event_loop()
        tasks = [self.async_chat(msgs, temperature) for msgs in messages_list]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [
            r if isinstance(r, str) else f"Error: {r}"
            for r in results
        ]

    def get_phantom_system_prompt(self) -> str:
        """Get PHANTOM system prompt."""
        return self.PHANTOM_SYSTEM_PROMPT

    def list_models(self) -> List[str]:
        """List available models for current backend."""
        if not self._available_models:
            self.detect_available_backends()
        return self._available_models.get(self.backend, [])

    def switch_model(self, model_name: str) -> bool:
        """Switch to a different model."""
        available = self.list_models()
        if model_name in available or model_name == "auto":
            self.model = model_name
            return True
        return False

    def estimate_tokens(self, text: str) -> int:
        """Rough token estimation."""
        return len(text) // 4

    def handle_error(self, exception: Exception) -> str:
        """Convert exception to user-friendly message."""
        error_str = str(exception).lower()
        
        if "authentication" in error_str or "401" in error_str:
            return "API key is invalid or expired. Please check your API key."
        if "rate limit" in error_str or "429" in error_str:
            return "Rate limit exceeded. Please wait a moment and try again."
        if "timeout" in error_str:
            return "Request timed out. The server may be busy. Please try again."
        if "connection" in error_str:
            return "Could not connect to the LLM service. Check your internet connection."
        
        return f"An error occurred: {exception}"

    def format_messages(self, user_input: str, context: Optional[str] = None) -> List[Dict[str, str]]:
        """Format messages for chat."""
        messages = [
            {"role": "system", "content": self.PHANTOM_SYSTEM_PROMPT}
        ]
        
        if context:
            messages.append({"role": "system", "content": f"Context from knowledge base:\n{context}"})
        
        messages.append({"role": "user", "content": user_input})
        
        return messages