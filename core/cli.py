"""PHANTOM CLI - Command-line interface with full system access."""

import os
import sys
import json
import time
import shlex
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from dataclasses import dataclass
import re

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax

logger = __import__("logging").getLogger("phantom.cli")


@dataclass
class CommandResult:
    """Result of a CLI command."""
    success: bool
    output: str
    error: str
    exit_code: int
    execution_time: float


@dataclass
class EditOperation:
    """File edit operation."""
    file_path: str
    operation: str
    details: str
    timestamp: str
    success: bool


class FileEditor:
    """PHANTOM's file editing capabilities."""

    BACKUP_ENABLED = True

    def __init__(self, backup_dir: Optional[Path] = None):
        """Initialize file editor."""
        self.backup_dir = backup_dir or (Path.home() / ".phantom" / "backups")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.operations: List[EditOperation] = []

    def read_file(self, path: str, limit: int = 0) -> Optional[str]:
        """Read file contents."""
        try:
            file_path = Path(path).expanduser()
            if not file_path.exists():
                return None

            content = file_path.read_text()

            if limit > 0 and len(content) > limit:
                return content[:limit] + f"\n... [+{len(content) - limit} chars]"

            return content
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
            file_path.write_text(content)

            self.operations.append(EditOperation(
                file_path=str(file_path),
                operation="write",
                details=f"Wrote {len(content)} bytes",
                timestamp=datetime.now().isoformat(),
                success=True
            ))

            return True
        except Exception as e:
            logger.error(f"Failed to write {path}: {e}")
            self.operations.append(EditOperation(
                file_path=path,
                operation="write",
                details=str(e),
                timestamp=datetime.now().isoformat(),
                success=False
            ))
            return False

    def append_file(self, path: str, content: str) -> bool:
        """Append content to file."""
        try:
            file_path = Path(path).expanduser()

            if file_path.exists():
                if self.BACKUP_ENABLED:
                    self._create_backup(file_path)
                existing = file_path.read_text()
                content = existing + "\n" + content
            else:
                file_path.parent.mkdir(parents=True, exist_ok=True)

            file_path.write_text(content)

            self.operations.append(EditOperation(
                file_path=str(file_path),
                operation="append",
                details=f"Appended {len(content)} bytes",
                timestamp=datetime.now().isoformat(),
                success=True
            ))

            return True
        except Exception as e:
            logger.error(f"Failed to append to {path}: {e}")
            return False

    def delete_file(self, path: str) -> bool:
        """Delete a file."""
        try:
            file_path = Path(path).expanduser()

            if not file_path.exists():
                return False

            if self.BACKUP_ENABLED:
                self._create_backup(file_path)

            file_path.unlink()

            self.operations.append(EditOperation(
                file_path=str(file_path),
                operation="delete",
                details="File deleted",
                timestamp=datetime.now().isoformat(),
                success=True
            ))

            return True
        except Exception as e:
            logger.error(f"Failed to delete {path}: {e}")
            return False

    def create_directory(self, path: str) -> bool:
        """Create directory."""
        try:
            dir_path = Path(path).expanduser()
            dir_path.mkdir(parents=True, exist_ok=True)

            self.operations.append(EditOperation(
                file_path=str(dir_path),
                operation="mkdir",
                details="Directory created",
                timestamp=datetime.now().isoformat(),
                success=True
            ))

            return True
        except Exception as e:
            logger.error(f"Failed to create directory {path}: {e}")
            return False

    def find_files(
        self,
        root: str,
        pattern: str = "*",
        max_depth: int = 5
    ) -> List[str]:
        """Find files matching pattern."""
        try:
            root_path = Path(root).expanduser()
            files = []

            for file_path in root_path.rglob(pattern):
                if file_path.is_file():
                    depth = len(file_path.relative_to(root_path).parts)
                    if depth <= max_depth:
                        files.append(str(file_path))

            return files
        except Exception as e:
            logger.error(f"Failed to find files: {e}")
            return []

    def replace_in_file(
        self,
        path: str,
        old: str,
        new: str,
        all_instances: bool = True
    ) -> Tuple[bool, int]:
        """Replace text in file."""
        try:
            file_path = Path(path).expanduser()

            if not file_path.exists():
                return False, 0

            if self.BACKUP_ENABLED:
                self._create_backup(file_path)

            content = file_path.read_text()

            if all_instances:
                count = content.count(old)
                new_content = content.replace(old, new)
            else:
                if old in content:
                    count = 1
                    new_content = content.replace(old, new, 1)
                else:
                    return False, 0

            file_path.write_text(new_content)

            self.operations.append(EditOperation(
                file_path=str(file_path),
                operation="replace",
                details=f"Replaced {count} instances of '{old[:30]}...'",
                timestamp=datetime.now().isoformat(),
                success=True
            ))

            return True, count
        except Exception as e:
            logger.error(f"Failed to replace in {path}: {e}")
            return False, 0

    def insert_in_file(
        self,
        path: str,
        content: str,
        after_line: int = -1,
        at_end: bool = True
    ) -> bool:
        """Insert content after specific line."""
        try:
            file_path = Path(path).expanduser()

            if not file_path.exists():
                return False

            if self.BACKUP_ENABLED:
                self._create_backup(file_path)

            lines = file_path.read_text().splitlines()

            if at_end or after_line < 0:
                lines.append(content)
            else:
                lines.insert(after_line + 1, content)

            file_path.write_text("\n".join(lines))

            self.operations.append(EditOperation(
                file_path=str(file_path),
                operation="insert",
                details=f"Inserted after line {after_line}",
                timestamp=datetime.now().isoformat(),
                success=True
            ))

            return True
        except Exception as e:
            logger.error(f"Failed to insert in {path}: {e}")
            return False

    def _create_backup(self, file_path: Path) -> Optional[Path]:
        """Create backup of file."""
        if not file_path.exists():
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{file_path.name}.{timestamp}.bak"
        backup_path = self.backup_dir / backup_name

        backup_path.write_bytes(file_path.read_bytes())

        return backup_path

    def get_file_info(self, path: str) -> Optional[Dict[str, Any]]:
        """Get file information."""
        try:
            file_path = Path(path).expanduser()

            if not file_path.exists():
                return None

            stat = file_path.stat()

            return {
                "path": str(file_path),
                "name": file_path.name,
                "size": stat.st_size,
                "size_human": self._human_size(stat.st_size),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "is_file": file_path.is_file(),
                "is_dir": file_path.is_dir(),
                "is_symlink": file_path.is_symlink(),
                "permissions": oct(stat.st_mode)[-3:],
            }
        except Exception as e:
            logger.error(f"Failed to get info for {path}: {e}")
            return None

    @staticmethod
    def _human_size(size: int) -> str:
        """Convert size to human-readable format."""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} PB"


class CommandRunner:
    """Execute system commands."""

    def __init__(self, timeout: int = 60, shell: str = "/bin/bash"):
        """Initialize command runner."""
        self.timeout = timeout
        self.shell = shell
        self.command_history: List[Dict[str, Any]] = []

    def run(
        self,
        command: str,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
        capture_output: bool = True
    ) -> CommandResult:
        """Execute a command."""
        start_time = time.time()

        try:
            full_env = os.environ.copy()
            if env:
                full_env.update(env)

            timeout_val = timeout or self.timeout

            if capture_output:
                result = subprocess.run(
                    command,
                    shell=True,
                    cwd=cwd,
                    env=full_env,
                    capture_output=True,
                    text=True,
                    timeout=timeout_val,
                )

                output = result.stdout
                error = result.stderr
                exit_code = result.returncode
            else:
                result = subprocess.run(
                    command,
                    shell=True,
                    cwd=cwd,
                    env=full_env,
                    timeout=timeout_val,
                )

                output = ""
                error = ""
                exit_code = result.returncode

            execution_time = time.time() - start_time

            self.command_history.append({
                "command": command,
                "exit_code": exit_code,
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat(),
            })

            return CommandResult(
                success=exit_code == 0,
                output=output,
                error=error,
                exit_code=exit_code,
                execution_time=execution_time
            )

        except subprocess.TimeoutExpired:
            return CommandResult(
                success=False,
                output="",
                error=f"Command timed out after {timeout_val}s",
                exit_code=-1,
                execution_time=time.time() - start_time
            )
        except Exception as e:
            return CommandResult(
                success=False,
                output="",
                error=str(e),
                exit_code=-1,
                execution_time=time.time() - start_time
            )

    def run_async(
        self,
        command: str,
        cwd: Optional[str] = None
    ) -> subprocess.Popen:
        """Run command asynchronously."""
        return subprocess.Popen(
            command,
            shell=True,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def get_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get command history."""
        return self.command_history[-limit:]


class CLI:
    """PHANTOM CLI interface."""

    def __init__(self, config: Optional["Config"] = None):
        """Initialize CLI."""
        self.config = config
        self.editor = FileEditor()
        self.runner = CommandRunner()
        self.console = Console()
        self._init_aliases()

    def _init_aliases(self) -> None:
        """Initialize command aliases."""
        self.aliases = {
            "ll": "ls -la",
            "la": "ls -A",
            "l": "ls -CF",
            "..": "cd ..",
            "...": "cd ../..",
            "py": "python3",
            "pip": "pip3",
            "grep": "grep --color=auto",
            "edit": "nano",
            "c": "clear",
            "exit": "quit",
        }

    def parse_and_execute(self, input_line: str) -> CommandResult:
        """Parse and execute CLI input."""
        input_line = input_line.strip()

        if not input_line:
            return CommandResult(success=True, output="", error="", exit_code=0, execution_time=0)

        parts = shlex.split(input_line, comments=True)
        if not parts:
            return CommandResult(success=True, output="", error="", exit_code=0, execution_time=0)

        command = parts[0]
        args = parts[1:]

        if command in self.aliases:
            full_command = self.aliases[command]
            if args:
                full_command += " " + " ".join(args)
            return self.runner.run(full_command)

        if command == "cd":
            if args:
                os.chdir(args[0])
                return CommandResult(
                    success=True,
                    output=f"Changed directory to {os.getcwd()}",
                    error="",
                    exit_code=0,
                    execution_time=0
                )
            return CommandResult(
                success=True,
                output=f"Current directory: {os.getcwd()}",
                error="",
                exit_code=0,
                execution_time=0
            )

        if command == "cat":
            if args:
                content = self.editor.read_file(args[0])
                if content:
                    return CommandResult(
                        success=True,
                        output=content,
                        error="",
                        exit_code=0,
                        execution_time=0
                    )
                return CommandResult(
                    success=False,
                    output="",
                    error=f"File not found: {args[0]}",
                    exit_code=1,
                    execution_time=0
                )
            return CommandResult(
                success=False,
                output="",
                error="Usage: cat <file>",
                exit_code=1,
                execution_time=0
            )

        if command == "pwd":
            return CommandResult(
                success=True,
                output=os.getcwd(),
                error="",
                exit_code=0,
                execution_time=0
            )

        if command == "edit" or command == "nano" or command == "vim":
            if args:
                file_path = args[0]
                content = self.editor.read_file(file_path)
                if content:
                    return CommandResult(
                        success=True,
                        output=f"File: {file_path}\n{content[:2000]}",
                        error="",
                        exit_code=0,
                        execution_time=0
                    )
            return CommandResult(
                success=True,
                output="Opening editor...",
                error="",
                exit_code=0,
                execution_time=0
            )

        if command == "mkdir":
            if args:
                success = self.editor.create_directory(args[0])
                return CommandResult(
                    success=success,
                    output=f"Created directory: {args[0]}" if success else "",
                    error="" if success else "Failed to create directory",
                    exit_code=0 if success else 1,
                    execution_time=0
                )
            return CommandResult(
                success=False,
                output="",
                error="Usage: mkdir <directory>",
                exit_code=1,
                execution_time=0
            )

        if command == "rm":
            if args:
                success = self.editor.delete_file(args[0])
                return CommandResult(
                    success=success,
                    output=f"Deleted: {args[0]}" if success else "",
                    error="" if success else "Failed to delete",
                    exit_code=0 if success else 1,
                    execution_time=0
                )
            return CommandResult(
                success=False,
                output="",
                error="Usage: rm <file>",
                exit_code=1,
                execution_time=0
            )

        if command == "find":
            if args:
                pattern = args[-1] if args else "*"
                root = args[0] if len(args) > 1 else "."
                files = self.editor.find_files(root, pattern)
                return CommandResult(
                    success=True,
                    output="\n".join(files) if files else "No files found",
                    error="",
                    exit_code=0,
                    execution_time=0
                )
            return CommandResult(
                success=True,
                output="\n".join(self.editor.find_files(".")),
                error="",
                exit_code=0,
                execution_time=0
            )

        if command == "info":
            if args:
                info = self.editor.get_file_info(args[0])
                if info:
                    output = "\n".join([f"{k}: {v}" for k, v in info.items()])
                    return CommandResult(
                        success=True,
                        output=output,
                        error="",
                        exit_code=0,
                        execution_time=0
                    )
                return CommandResult(
                    success=False,
                    output="",
                    error=f"File not found: {args[0]}",
                    exit_code=1,
                    execution_time=0
                )
            return CommandResult(
                success=False,
                output="",
                error="Usage: info <file>",
                exit_code=1,
                execution_time=0
            )

        return self.runner.run(input_line)

    def execute_file_edit(
        self,
        file_path: str,
        operation: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Execute specific file operation."""
        if operation == "read":
            content = self.editor.read_file(file_path, limit=kwargs.get("limit", 0))
            return {"success": bool(content), "content": content}

        if operation == "write":
            content = kwargs.get("content", "")
            success = self.editor.write_file(file_path, content)
            return {"success": success}

        if operation == "append":
            content = kwargs.get("content", "")
            success = self.editor.append_file(file_path, content)
            return {"success": success}

        if operation == "delete":
            success = self.editor.delete_file(file_path)
            return {"success": success}

        if operation == "replace":
            old = kwargs.get("old", "")
            new = kwargs.get("new", "")
            all_inst = kwargs.get("all", True)
            success, count = self.editor.replace_in_file(file_path, old, new, all_inst)
            return {"success": success, "count": count}

        if operation == "insert":
            content = kwargs.get("content", "")
            after = kwargs.get("after_line", -1)
            at_end = kwargs.get("at_end", True)
            success = self.editor.insert_in_file(file_path, content, after, at_end)
            return {"success": success}

        if operation == "info":
            info = self.editor.get_file_info(file_path)
            return {"success": bool(info), "info": info}

        return {"success": False, "error": f"Unknown operation: {operation}"}

    def display_file(self, path: str, syntax: str = "python") -> None:
        """Display file with syntax highlighting."""
        content = self.editor.read_file(path)

        if content:
            syntax_obj = Syntax(content, syntax, line_numbers=True)
            self.console.print(syntax_obj)
        else:
            self.console.print(f"[red]File not found: {path}[/red]")

    def display_directory(self, path: str = ".") -> None:
        """Display directory contents."""
        try:
            dir_path = Path(path).expanduser()

            table = Table(title=f"Directory: {dir_path}")
            table.add_column("Type", width=1)
            table.add_column("Name", style="cyan")
            table.add_column("Size", style="green")
            table.add_column("Modified")

            for item in sorted(dir_path.iterdir()):
                stat = item.stat()
                size = self.editor._human_size(stat.st_size)
                mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")

                if item.is_dir():
                    table.add_row("d", f"[bold blue]{item.name}[/bold blue]", "-", mtime)
                elif item.is_symlink():
                    table.add_row("l", f"[bold cyan]{item.name}[/bold cyan]", "-", mtime)
                else:
                    table.add_row("-", item.name, size, mtime)

            self.console.print(table)
        except Exception as e:
            self.console.print(f"[red]Error: {e}[/red]")

    def get_capabilities(self) -> Dict[str, Any]:
        """Get CLI capabilities."""
        return {
            "file_operations": [
                "read", "write", "append", "delete",
                "replace", "insert", "mkdir", "find", "info"
            ],
            "shell_commands": True,
            "sudo_access": True,
            "git_operations": True,
            "package_management": True,
            "system_info": True,
        }


def create_cli(config: Optional["Config"] = None) -> CLI:
    """Create CLI instance."""
    return CLI(config=config)