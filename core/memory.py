"""Conversation Memory - Session and context management."""

import json
import logging
import time
import uuid
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime

from core.config import Config

logger = logging.getLogger("phantom.memory")


@dataclass
class Message:
    """Chat message."""
    role: str
    content: str
    timestamp: str = ""
    tokens: int = 0
    thinking_mode: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
            "tokens": self.tokens,
            "thinking_mode": self.thinking_mode,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """Create from dictionary."""
        return cls(
            role=data.get("role", "user"),
            content=data.get("content", ""),
            timestamp=data.get("timestamp", ""),
            tokens=data.get("tokens", 0),
            thinking_mode=data.get("thinking_mode"),
        )


class ConversationMemory:
    """Conversation and session memory."""

    def __init__(self, config: Optional[Config] = None):
        """Initialize conversation memory."""
        self.config = config or Config.get_instance()
        self.messages: List[Message] = []
        self.session_id: str = ""
        self.max_context_tokens: int = 4096

        self._sessions_dir = self.config.config_dir / "sessions"
        self._sessions_dir.mkdir(parents=True, exist_ok=True)

    def add(
        self,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add message to conversation."""
        if not self.session_id:
            self.session_id = str(uuid.uuid4())[:8]

        message = Message(
            role=role,
            content=content,
            timestamp=datetime.now().isoformat(),
            tokens=len(content) // 4,
            thinking_mode=metadata.get("thinking_mode") if metadata else None,
        )

        self.messages.append(message)

        if len(self.messages) > 1000:
            self.messages = self.messages[-500:]

    def get_window(self, max_tokens: Optional[int] = None) -> List[Dict[str, str]]:
        """Get recent messages within token limit."""
        if max_tokens is None:
            max_tokens = self.max_context_tokens

        result: List[Dict[str, str]] = []
        current_tokens = 0

        for message in reversed(self.messages):
            msg_tokens = message.tokens
            if current_tokens + msg_tokens > max_tokens:
                break

            result.insert(0, message.to_dict())
            current_tokens += msg_tokens

        return result

    def summarize_old_context(self) -> str:
        """Summarize older context."""
        if len(self.messages) <= 10:
            return ""

        old_messages = self.messages[:-10]
        summary = []

        for msg in old_messages:
            preview = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
            summary.append(f"[{msg.role.upper()}]: {preview}")

        return "\n".join(summary)

    def save(self, session_id: Optional[str] = None) -> str:
        """Save current session."""
        if session_id:
            self.session_id = session_id

        if not self.session_id:
            self.session_id = str(uuid.uuid4())[:8]

        session_file = self._sessions_dir / f"{self.session_id}.json"

        data = {
            "session_id": self.session_id,
            "messages": [msg.to_dict() for msg in self.messages],
            "saved_at": datetime.now().isoformat(),
        }

        with open(session_file, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Saved session {self.session_id}")
        return self.session_id

    def load(self, session_id: str) -> bool:
        """Load a session."""
        session_file = self._sessions_dir / f"{session_id}.json"

        if not session_file.exists():
            return False

        try:
            with open(session_file) as f:
                data = json.load(f)

            self.session_id = data.get("session_id", session_id)
            self.messages = [
                Message.from_dict(msg) for msg in data.get("messages", [])
            ]

            logger.info(f"Loaded session {session_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to load session: {e}")
            return False

    def load_latest_session(self) -> bool:
        """Load the most recent session."""
        sessions = list(self._sessions_dir.glob("*.json"))

        if not sessions:
            return False

        latest = max(sessions, key=lambda p: p.stat().st_mtime)
        session_id = latest.stem

        return self.load(session_id)

    def search(self, query: str) -> List[Dict[str, Any]]:
        """Search through conversation history."""
        query_lower = query.lower()
        results = []

        for message in self.messages:
            if query_lower in message.content.lower():
                results.append(message.to_dict())

            if len(results) >= 20:
                break

        return results

    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all saved sessions."""
        sessions = []

        for session_file in self._sessions_dir.glob("*.json"):
            try:
                mtime = datetime.fromtimestamp(
                    session_file.stat().st_mtime
                ).isoformat()

                with open(session_file) as f:
                    data = json.load(f)

                msg_count = len(data.get("messages", []))

                sessions.append({
                    "id": session_file.stem,
                    "date": mtime,
                    "message_count": msg_count,
                })

            except Exception:
                pass

        sessions.sort(key=lambda x: x["date"], reverse=True)
        return sessions

    def clear(self) -> None:
        """Clear current conversation."""
        self.messages.clear()
        logger.info("Cleared conversation memory")

    def new_session(self) -> str:
        """Start a new session."""
        self.save()
        self.session_id = str(uuid.uuid4())[:8]
        self.messages.clear()
        logger.info(f"Started new session {self.session_id}")
        return self.session_id