"""PHANTOM Self-Update Engine - Auto-updates and self-modification."""

import os
import re
import json
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import hashlib
import shutil

from core.config import Config

import logging

logger = logging.getLogger("phantom.updater")


@dataclass
class UpdateResult:
    """Result of update operation."""
    success: bool
    version_before: str
    version_after: str
    files_updated: int
    changes: List[str]
    rollback_available: bool


@dataclass
class VersionInfo:
    """Version information."""
    major: int
    minor: int
    patch: int
    suffix: str
    full_version: str


class VersionManager:
    """Manage PHANTOM version tracking."""

    def __init__(self, config: Optional[Config] = None):
        """Initialize version manager."""
        self.config = config or Config.get_instance()
        self.current_version = self._parse_version(self._get_version_string())

    def _get_version_string(self) -> str:
        """Get current version string."""
        try:
            version_file = Path(__file__).parent.parent / "VERSION"
            if version_file.exists():
                return version_file.read_text().strip()
        except Exception:
            pass
        return "2.0.1"

    def _parse_version(self, version_str: str) -> VersionInfo:
        """Parse version string."""
        match = re.match(r"(\d+)\.(\d+)\.(\d+)(?:-(\w+))?", version_str)
        if match:
            return VersionInfo(
                major=int(match.group(1)),
                minor=int(match.group(2)),
                patch=int(match.group(3)),
                suffix=match.group(4) or "",
                full_version=version_str
            )
        return VersionInfo(2, 0, 1, "", version_str)

    def compare_versions(self, v1: str, v2: str) -> int:
        """Compare two versions. Returns -1, 0, or 1."""
        ver1 = self._parse_version(v1)
        ver2 = self._parse_version(v2)

        for attr in ["major", "minor", "patch"]:
            if getattr(ver1, attr) < getattr(ver2, attr):
                return -1
            elif getattr(ver1, attr) > getattr(ver2, attr):
                return 1
        return 0

    def get_current_version(self) -> str:
        """Get current version."""
        return self.current_version.full_version

    def bump_version(self, level: str = "patch") -> str:
        """Bump version number."""
        v = self.current_version

        if level == "major":
            v.major += 1
            v.minor = 0
            v.patch = 0
        elif level == "minor":
            v.minor += 1
            v.patch = 0
        else:
            v.patch += 1

        v.full_version = f"{v.major}.{v.minor}.{v.patch}{v.suffix}"
        return v.full_version


class CodeEditor:
    """PHANTOM's code editing capabilities."""

    BACKUP_ENABLED = True
    VALID_LANGUAGES = {
        "py": "python", "python": "python",
        "js": "javascript", "javascript": "javascript",
        "ts": "typescript", "typescript": "typescript",
        "rs": "rust", "rust": "rust",
        "go": "go", "go": "go",
        "c": "c", "c": "c",
        "cpp": "cpp", "cpp": "cpp",
        "java": "java", "java": "java",
        "sh": "bash", "bash": "bash",
        "rb": "ruby", "ruby": "ruby",
        "php": "php", "php": "php",
        "html": "html", "html": "html",
        "css": "css", "css": "css",
        "sql": "sql", "sql": "sql",
        "json": "json", "json": "json",
        "yaml": "yaml", "yaml": "yaml",
        "md": "markdown", "markdown": "markdown",
    }

    def __init__(self, backup_dir: Optional[Path] = None):
        """Initialize code editor."""
        self.backup_dir = backup_dir or (Path.home() / ".phantom" / "backups")
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def get_language(self, file_path: str) -> str:
        """Detect programming language from file extension."""
        ext = Path(file_path).suffix.lstrip(".")
        return self.VALID_LANGUAGES.get(ext, "text")

    def read_file(self, path: str) -> Optional[str]:
        """Read file contents."""
        try:
            file_path = Path(path).expanduser()
            if file_path.exists():
                return file_path.read_text(encoding="utf-8")
        except Exception as e:
            logger.error(f"Failed to read {path}: {e}")
        return None

    def write_file(self, path: str, content: str, create: bool = True) -> bool:
        """Write content to file."""
        try:
            file_path = Path(path).expanduser()

            if not file_path.exists() and not create:
                return False

            if self.BACKUP_ENABLED and file_path.exists():
                self._create_backup(file_path)

            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")

            logger.info(f"Wrote {len(content)} bytes to {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to write {path}: {e}")
            return False

    def replace_in_file(
        self,
        path: str,
        old: str,
        new: str,
        all_instances: bool = True
    ) -> Tuple[bool, int]:
        """Replace text in file."""
        content = self.read_file(path)
        if content is None:
            return False, 0

        if all_instances:
            count = content.count(old)
            new_content = content.replace(old, new)
        else:
            if old in content:
                count = 1
                new_content = content.replace(old, new, 1)
            else:
                return False, 0

        success = self.write_file(path, new_content)
        return success, count

    def insert_at_line(
        self,
        path: str,
        content: str,
        line_number: int
    ) -> bool:
        """Insert content at specific line."""
        lines = self.read_file(path)
        if lines is None:
            return False

        lines_list = lines.splitlines()
        lines_list.insert(line_number - 1, content)
        return self.write_file(path, "\n".join(lines_list))

    def delete_lines(
        self,
        path: str,
        start: int,
        end: int
    ) -> bool:
        """Delete lines in file."""
        lines = self.read_file(path)
        if lines is None:
            return False

        lines_list = lines.splitlines()
        del lines_list[start - 1:end]
        return self.write_file(path, "\n".join(lines_list))

    def add_function(
        self,
        path: str,
        name: str,
        params: str,
        body: str,
        language: Optional[str] = None
    ) -> bool:
        """Add a function to file."""
        lang = language or self.get_language(path)

        if lang == "python":
            func = f"\ndef {name}({params}):\n{body}\n\n"
        elif lang in ("javascript", "typescript"):
            func = f"\nfunction {name}({params}) {{\n{body}\n}}\n\n"
        elif lang == "go":
            func = f"\nfunc {name}({params}) {{\n{body}\n}}\n\n"
        elif lang == "rust":
            func = f"\nfn {name}({params}) {{\n{body}\n}}\n\n"
        elif lang in ("c", "cpp"):
            func = f"\nvoid {name}({params}) {{\n{body}\n}}\n\n"
        else:
            func = f"\n{name}({params}) {{\n{body}\n}}\n\n"

        content = self.read_file(path) or ""
        return self.write_file(path, content + func)

    def add_class(
        self,
        path: str,
        name: str,
        methods: List[Dict[str, str]],
        language: Optional[str] = None
    ) -> bool:
        """Add a class to file."""
        lang = language or self.get_language(path)

        if lang == "python":
            class_code = f"\nclass {name}:\n"
            for method in methods:
                class_code += f"    def {method['name']}({method.get('params', '')}):\n"
                class_code += f"{method.get('body', 'pass')}\n\n"
            class_code += "\n"
        elif lang in ("javascript", "typescript"):
            class_code = f"\nclass {name} {{\n"
            for method in methods:
                class_code += f"    {method['name']}({method.get('params', '')}) {{\n"
                class_code += f"{method.get('body', '}')\n"
            class_code += "}\n\n"
        else:
            class_code = f"\n/* {name} class */\n"

        content = self.read_file(path) or ""
        return self.write_file(path, content + class_code)

    def find_function(
        self,
        path: str,
        name: str
    ) -> Optional[Dict[str, Any]]:
        """Find function definition in file."""
        content = self.read_file(path)
        if not content:
            return None

        lang = self.get_language(path)

        if lang == "python":
            pattern = rf"def {name}\s*\(([^)]*)\):"
        elif lang in ("javascript", "typescript"):
            pattern = rf"(?:async\s+)?function\s+{name}\s*\(([^)]*)\)"
        elif lang == "go":
            pattern = rf"func\s+{name}\s*\(([^)]*)\)"
        elif lang == "rust":
            pattern = rf"fn\s+{name}\s*\(([^)]*)\)"
        else:
            pattern = rf"{name}\s*\(([^)]*)\)"

        match = re.search(pattern, content)
        if match:
            return {
                "name": name,
                "params": match.group(1) if match.lastindex else "",
                "line": content[:match.start()].count("\n") + 1
            }
        return None

    def get_file_hash(self, path: str) -> Optional[str]:
        """Get SHA256 hash of file."""
        try:
            file_path = Path(path).expanduser()
            if file_path.exists():
                return hashlib.sha256(file_path.read_bytes()).hexdigest()
        except Exception:
            pass
        return None

    def _create_backup(self, file_path: Path) -> Optional[Path]:
        """Create backup of file."""
        if not file_path.exists():
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{file_path.name}.{timestamp}.bak"
        backup_path = self.backup_dir / backup_name

        backup_path.write_bytes(file_path.read_bytes())
        return backup_path


class SelfUpdater:
    """PHANTOM can update itself."""

    def __init__(
        self,
        config: Optional[Config] = None,
        code_editor: Optional[CodeEditor] = None
    ):
        """Initialize self-updater."""
        self.config = config or Config.get_instance()
        self.editor = code_editor or CodeEditor()
        self.version_manager = VersionManager(config)

        self.update_dir = self.config.config_dir / "updates"
        self.update_dir.mkdir(parents=True, exist_ok=True)

        self._changelog: List[Dict[str, str]] = []

    def check_for_updates(self) -> Dict[str, Any]:
        """Check for available updates."""
        current = self.version_manager.get_current_version()

        return {
            "current_version": current,
            "up_to_date": True,
            "last_checked": datetime.now().isoformat(),
        }

    def apply_update(
        self,
        file_path: str,
        patches: List[Dict[str, str]]
    ) -> UpdateResult:
        """Apply code patches."""
        version_before = self.version_manager.get_current_version()
        changes = []

        for patch in patches:
            old = patch.get("old", "")
            new = patch.get("new", "")
            op = patch.get("operation", "replace")

            if op == "replace":
                success, count = self.editor.replace_in_file(file_path, old, new)
                if success:
                    changes.append(f"Replaced {count}x: {old[:30]}...")

            elif op == "insert":
                line = patch.get("line", 1)
                success = self.editor.insert_at_line(file_path, new, line)
                if success:
                    changes.append(f"Inserted at line {line}")

            elif op == "delete":
                start = patch.get("start", 1)
                end = patch.get("end", start)
                success = self.editor.delete_lines(file_path, start, end)
                if success:
                    changes.append(f"Deleted lines {start}-{end}")

        version_after = self.version_manager.get_current_version()

        return UpdateResult(
            success=len(changes) > 0,
            version_before=version_before,
            version_after=version_after,
            files_updated=len(changes),
            changes=changes,
            rollback_available=True
        )

    def modify_source(
        self,
        module: str,
        modification: Dict[str, Any]
    ) -> bool:
        """Modify PHANTOM source code."""
        base_path = Path(__file__).parent.parent
        file_path = base_path / module

        if not file_path.exists():
            return False

        op = modification.get("operation")

        if op == "add_function":
            return self.editor.add_function(
                str(file_path),
                modification["name"],
                modification.get("params", ""),
                modification.get("body", "pass"),
            )

        elif op == "add_class":
            return self.editor.add_class(
                str(file_path),
                modification["name"],
                modification.get("methods", []),
            )

        elif op == "patch":
            old = modification.get("old")
            new = modification.get("new")
            if old and new:
                success, _ = self.editor.replace_in_file(str(file_path), old, new)
                return success

        return False

    def get_source_info(self, module: str) -> Optional[Dict[str, Any]]:
        """Get information about source module."""
        base_path = Path(__file__).parent.parent
        file_path = base_path / module

        if not file_path.exists():
            return None

        content = self.editor.read_file(str(file_path))
        if not content:
            return None

        lang = self.editor.get_language(str(file_path))

        functions = []
        if lang == "python":
            for match in re.finditer(r"def\s+(\w+)\s*\(([^)]*)\)", content):
                functions.append({
                    "name": match.group(1),
                    "params": match.group(2),
                    "line": content[:match.start()].count("\n") + 1
                })

        classes = []
        if lang == "python":
            for match in re.finditer(r"class\s+(\w+)(?:\([^)]*\))?:", content):
                classes.append({
                    "name": match.group(1),
                    "line": content[:match.start()].count("\n") + 1
                })

        lines = len(content.splitlines())
        chars = len(content)

        return {
            "module": module,
            "path": str(file_path),
            "language": lang,
            "lines": lines,
            "characters": chars,
            "functions": functions,
            "classes": classes,
            "hash": self.editor.get_file_hash(str(file_path)),
        }

    def add_changelog_entry(self, entry: str, severity: str = "minor") -> None:
        """Add entry to changelog."""
        self._changelog.append({
            "entry": entry,
            "severity": severity,
            "timestamp": datetime.now().isoformat(),
        })

    def get_changelog(self) -> str:
        """Get formatted changelog."""
        output = "# PHANTOM Changelog\n\n"

        for entry in reversed(self._changelog[-20:]):
            output += f"- [{entry['severity'].upper()}] {entry['entry']}\n"
            output += f"  {entry['timestamp'][:10]}\n\n"

        return output

    def create_patch(
        self,
        file_path: str,
        old_content: str,
        new_content: str,
        description: str
    ) -> Dict[str, Any]:
        """Create a patch for later application."""
        patch = {
            "file": file_path,
            "old": old_content,
            "new": new_content,
            "description": description,
            "created": datetime.now().isoformat(),
            "hash_before": hashlib.sha256(old_content.encode()).hexdigest(),
            "hash_after": hashlib.sha256(new_content.encode()).hexdigest(),
        }

        patch_file = self.update_dir / f"patch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        patch_file.write_text(json.dumps(patch, indent=2))

        return patch

    def verify_integrity(self) -> bool:
        """Verify PHANTOM source integrity."""
        base_path = Path(__file__).parent.parent

        integrity_file = self.config.config_dir / "integrity.json"
        if not integrity_file.exists():
            return True

        try:
            data = json.loads(integrity_file.read_text())
            stored_hashes = data.get("hashes", {})

            for module, stored_hash in stored_hashes.items():
                file_path = base_path / module
                if file_path.exists():
                    current_hash = self.editor.get_file_hash(str(file_path))
                    if current_hash != stored_hash:
                        logger.warning(f"Hash mismatch for {module}")
                        return False

            return True
        except Exception as e:
            logger.error(f"Integrity check failed: {e}")
            return False

    def save_integrity(self) -> None:
        """Save source file hashes."""
        base_path = Path(__file__).parent.parent
        hashes = {}

        for py_file in base_path.rglob("*.py"):
            if "__pycache__" not in str(py_file):
                rel_path = py_file.relative_to(base_path)
                file_hash = self.editor.get_file_hash(str(py_file))
                if file_hash:
                    hashes[str(rel_path)] = file_hash

        integrity_file = self.config.config_dir / "integrity.json"
        integrity_file.write_text(json.dumps({"hashes": hashes}, indent=2))