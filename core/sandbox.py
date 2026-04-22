"""PHANTOM Sandbox - Secure code execution environment."""

import os
import re
import json
import subprocess
import tempfile
import time
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
from contextlib import contextmanager

from core.config import Config

import logging

logger = logging.getLogger("phantom.sandbox")


@dataclass
class ExecutionResult:
    """Result of sandboxed execution."""
    success: bool
    output: str
    error: str
    exit_code: int
    execution_time: float
    memory_usage: int
    language: str


@dataclass
class SandboxConfig:
    """Sandbox configuration."""
    timeout: int = 30
    memory_limit: int = 256 * 1024 * 1024
    max_output_size: int = 1024 * 1024
    max_file_size: int = 10 * 1024 * 1024
    allow_network: bool = False
    allow_filesystem: bool = True
    allowed_paths: List[str] = None
    block_patterns: List[str] = None

    def __post_init__(self):
        if self.allowed_paths is None:
            self.allowed_paths = ["/tmp", "/dev/null"]
        if self.block_patterns is None:
            self.block_patterns = [
                r"rm\s+-rf\s+/",
                r"format\s+c:",
                r"dd\s+if=",
                r"mkfs",
                r"del\s+/[sr]",
            ]


class Sandbox:
    """Secure code execution sandbox."""

    LANGUAGES = {
        "python": {
            "extension": ".py",
            "command": ["python3", "-u", "{file}"],
            "compile": None,
        },
        "python2": {
            "extension": ".py",
            "command": ["python2", "-u", "{file}"],
            "compile": None,
        },
        "javascript": {
            "extension": ".js",
            "command": ["node", "{file}"],
            "compile": None,
        },
        "bash": {
            "extension": ".sh",
            "command": ["bash", "{file}"],
            "compile": None,
        },
        "shell": {
            "extension": ".sh",
            "command": ["/bin/bash", "{file}"],
            "compile": None,
        },
        "ruby": {
            "extension": ".rb",
            "command": ["ruby", "{file}"],
            "compile": None,
        },
        "perl": {
            "extension": ".pl",
            "command": ["perl", "{file}"],
            "compile": None,
        },
        "php": {
            "extension": ".php",
            "command": ["php", "{file}"],
            "compile": None,
        },
        "lua": {
            "extension": ".lua",
            "command": ["lua", "{file}"],
            "compile": None,
        },
        "awk": {
            "extension": ".awk",
            "command": ["awk", "-f", "{file}"],
            "compile": None,
        },
        "sed": {
            "extension": ".sed",
            "command": ["sed", "-f", "{file}"],
            "compile": None,
        },
        "sql": {
            "extension": ".sql",
            "command": ["sqlite3", ":memory:"],
            "compile": None,
        },
    }

    def __init__(
        self,
        config: Optional[Config] = None,
        sandbox_config: Optional[SandboxConfig] = None
    ):
        """Initialize sandbox."""
        self.config = config or Config.get_instance()
        self.sandbox_config = sandbox_config or SandboxConfig()

        self.work_dir = Path(tempfile.mkdtemp(prefix="phantom_sandbox_"))
        self.config_dir = self.config.config_dir / "sandbox"
        self.config_dir.mkdir(parents=True, exist_ok=True)

        self._execution_history: List[Dict[str, Any]] = []

    def __del__(self):
        """Cleanup on deletion."""
        self.cleanup()

    def cleanup(self) -> None:
        """Remove sandbox directory."""
        try:
            if self.work_dir.exists():
                shutil.rmtree(self.work_dir, ignore_errors=True)
        except Exception as e:
            logger.debug(f"Sandbox cleanup error: {e}")

    def validate_code(self, code: str, language: str) -> Tuple[bool, str]:
        """Validate code for safety."""
        if language not in self.LANGUAGES:
            return False, f"Unsupported language: {language}"

        for pattern in self.sandbox_config.block_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                return False, f"Blocked pattern detected: {pattern}"

        if len(code) > self.sandbox_config.max_file_size:
            return False, f"Code too large: {len(code)} > {self.sandbox_config.max_file_size}"

        return True, "OK"

    def execute(
        self,
        code: str,
        language: str = "python",
        stdin: str = "",
        **kwargs
    ) -> ExecutionResult:
        """Execute code in sandbox."""
        start_time = time.time()

        if language not in self.LANGUAGES:
            return ExecutionResult(
                success=False,
                output="",
                error=f"Unsupported language: {language}",
                exit_code=-1,
                execution_time=0,
                memory_usage=0,
                language=language
            )

        valid, message = self.validate_code(code, language)
        if not valid:
            return ExecutionResult(
                success=False,
                output="",
                error=message,
                exit_code=-1,
                execution_time=0,
                memory_usage=0,
                language=language
            )

        lang_config = self.LANGUAGES[language]
        extension = lang_config["extension"]

        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=extension,
            dir=self.work_dir,
            delete=False,
            encoding="utf-8"
        ) as f:
            f.write(code)
            file_path = f.name

        try:
            command = [arg.replace("{file}", file_path) for arg in lang_config["command"]]

            result = subprocess.run(
                command,
                input=stdin,
                capture_output=True,
                text=True,
                timeout=self.sandbox_config.timeout,
                cwd=self.work_dir,
                env=self._create_environment(),
            )

            output = result.stdout[:self.sandbox_config.max_output_size]
            error = result.stderr[:self.sandbox_config.max_output_size]

            execution_time = time.time() - start_time

            self._execution_history.append({
                "language": language,
                "success": result.returncode == 0,
                "exit_code": result.returncode,
                "execution_time": execution_time,
                "output_size": len(output),
                "timestamp": datetime.now().isoformat(),
            })

            return ExecutionResult(
                success=result.returncode == 0,
                output=output,
                error=error,
                exit_code=result.returncode,
                execution_time=execution_time,
                memory_usage=0,
                language=language
            )

        except subprocess.TimeoutExpired:
            return ExecutionResult(
                success=False,
                output="",
                error=f"Execution timed out after {self.sandbox_config.timeout}s",
                exit_code=-1,
                execution_time=time.time() - start_time,
                memory_usage=0,
                language=language
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                output="",
                error=str(e),
                exit_code=-1,
                execution_time=time.time() - start_time,
                memory_usage=0,
                language=language
            )
        finally:
            try:
                Path(file_path).unlink(missing_ok=True)
            except Exception:
                pass

    def execute_file(
        self,
        file_path: str,
        language: Optional[str] = None,
        **kwargs
    ) -> ExecutionResult:
        """Execute file in sandbox."""
        try:
            file_path = Path(file_path).expanduser()

            if not file_path.exists():
                return ExecutionResult(
                    success=False,
                    output="",
                    error=f"File not found: {file_path}",
                    exit_code=-1,
                    execution_time=0,
                    memory_usage=0,
                    language=language or "unknown"
                )

            code = file_path.read_text(encoding="utf-8")

            if language is None:
                ext = file_path.suffix.lstrip(".")
                language = ext if ext in self.LANGUAGES else "unknown"

            return self.execute(code, language, **kwargs)

        except Exception as e:
            return ExecutionResult(
                success=False,
                output="",
                error=str(e),
                exit_code=-1,
                execution_time=0,
                memory_usage=0,
                language=language or "unknown"
            )

    def _create_environment(self) -> Dict[str, str]:
        """Create sandboxed environment."""
        env = os.environ.copy()

        env["HOME"] = str(self.work_dir)
        env["TMPDIR"] = str(self.work_dir)
        env["TMP"] = str(self.work_dir)
        env["TEMP"] = str(self.work_dir)

        if not self.sandbox_config.allow_network:
            env.pop("HTTP_PROXY", None)
            env.pop("HTTPS_PROXY", None)
            env.pop("http_proxy", None)
            env.pop("https_proxy", None)

        return env

    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        return list(self.LANGUAGES.keys())

    def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution statistics."""
        total = len(self._execution_history)
        successful = sum(1 for e in self._execution_history if e["success"])

        return {
            "total_executions": total,
            "successful": successful,
            "success_rate": f"{successful/total*100:.0f}%" if total > 0 else "0%",
            "total_time": sum(e["execution_time"] for e in self._execution_history),
            "languages_used": list(set(e["language"] for e in self._execution_history)),
        }

    def save_session(self, name: str = "default") -> str:
        """Save execution session."""
        session_file = self.config_dir / f"session_{name}.json"

        session_file.write_text(json.dumps({
            "name": name,
            "history": self._execution_history,
            "saved_at": datetime.now().isoformat(),
        }, indent=2))

        return str(session_file)

    def load_session(self, name: str = "default") -> bool:
        """Load execution session."""
        session_file = self.config_dir / f"session_{name}.json"

        if not session_file.exists():
            return False

        try:
            data = json.loads(session_file.read_text())
            self._execution_history = data.get("history", [])
            return True
        except Exception as e:
            logger.error(f"Failed to load session: {e}")
            return False


@contextmanager
def temporary_sandbox(timeout: int = 30):
    """Context manager for temporary sandbox."""
    sandbox = Sandbox()
    try:
        yield sandbox
    finally:
        sandbox.cleanup()


def quick_execute(
    code: str,
    language: str = "python",
    timeout: int = 30
) -> Tuple[bool, str, str]:
    """Quick execute without full sandbox setup."""
    with temporary_sandbox(timeout) as sandbox:
        sandbox.sandbox_config.timeout = timeout
        result = sandbox.execute(code, language)

        return result.success, result.output, result.error