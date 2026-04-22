"""Session Manager - Handles session lifecycle."""

import json
import logging
import uuid
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from core.config import Config

logger = logging.getLogger("phantom.session")


class Session:
    """Session container."""
    def __init__(
        self,
        session_id: str,
        created_at: str,
        last_active: str,
        message_count: int,
        platform: str
    ):
        self.session_id = session_id
        self.created_at = created_at
        self.last_active = last_active
        self.message_count = message_count
        self.platform = platform


class SessionManager:
    """Manage session lifecycle."""

    def __init__(self, config: Optional[Config] = None):
        """Initialize session manager."""
        self.config = config or Config.get_instance()
        self.current_session: Optional[Session] = None

        self._sessions_dir = self.config.config_dir / "sessions"
        self._sessions_dir.mkdir(parents=True, exist_ok=True)

    def create_session(self, platform: str = "unknown") -> Session:
        """Create new session."""
        session_id = str(uuid.uuid4())[:8]
        now = datetime.now().isoformat()

        session = Session(
            session_id=session_id,
            created_at=now,
            last_active=now,
            message_count=0,
            platform=platform
        )

        self.current_session = session
        self._save_session(session)

        logger.info(f"Created session {session_id}")
        return session

    def _save_session(self, session: Session) -> None:
        """Save session metadata."""
        session_file = self._sessions_dir / f"{session.session_id}.meta.json"

        data = {
            "session_id": session.session_id,
            "created_at": session.created_at,
            "last_active": session.last_active,
            "message_count": session.message_count,
            "platform": session.platform,
        }

        with open(session_file, "w") as f:
            json.dump(data, f, indent=2)

    def load_session(self, session_id: str) -> Optional[Session]:
        """Load session metadata."""
        session_file = self._sessions_dir / f"{session_id}.meta.json"

        if not session_file.exists():
            return None

        try:
            with open(session_file) as f:
                data = json.load(f)

            session = Session(
                session_id=data["session_id"],
                created_at=data["created_at"],
                last_active=data["last_active"],
                message_count=data["message_count"],
                platform=data.get("platform", "unknown"),
            )

            self.current_session = session
            return session

        except Exception as e:
            logger.error(f"Failed to load session: {e}")
            return None

    def update_session(self) -> None:
        """Update current session."""
        if self.current_session:
            self.current_session.last_active = datetime.now().isoformat()
            self._save_session(self.current_session)

    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all sessions."""
        sessions = []

        for meta_file in self._sessions_dir.glob("*.meta.json"):
            try:
                with open(meta_file) as f:
                    data = json.load(f)
                sessions.append(data)
            except Exception:
                pass

        sessions.sort(
            key=lambda x: x.get("last_active", ""),
            reverse=True
        )

        return sessions

    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        try:
            (self._sessions_dir / f"{session_id}.meta.json").unlink()
            (self._sessions_dir / f"{session_id}.json").unlink()
            logger.info(f"Deleted session {session_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete session: {e}")
            return False