"""Terminal - Rich UI components."""

from typing import Optional, List, Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.align import Align

from ui.themes import get_theme


class Terminal:
    """Rich terminal UI components."""

    def __init__(self, theme_name: str = "matrix"):
        """Initialize terminal."""
        self.theme = get_theme(theme_name)
        self.console = Console()

    def print(self, *args, **kwargs) -> None:
        """Print to terminal."""
        self.console.print(*args, **kwargs)

    def print_panel(
        self,
        content: str,
        title: Optional[str] = None,
        style: str = "green"
    ) -> None:
        """Print panel."""
        self.console.print(Panel(content, title=title, border_style=style))

    def print_table(
        self,
        headers: List[str],
        rows: List[List[str]],
        title: Optional[str] = None
    ) -> None:
        """Print table."""
        table = Table(title=title, show_header=True)

        for i, header in enumerate(headers):
            style = "cyan" if i == 0 else "green"
            table.add_column(header, style=style)

        for row in rows:
            table.add_row(*[str(c) for c in row])

        self.console.print(table)

    def print_tree(
        self,
        data: Dict[str, Any],
        title: str = "Tree"
    ) -> None:
        """Print tree structure."""
        tree = Tree(title)

        def add_nodes(parent: Tree, data: Any) -> None:
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, (dict, list)):
                        child = parent.add(f"[cyan]{key}[/cyan]")
                        add_nodes(child, value)
                    else:
                        parent.add(f"[cyan]{key}:[/cyan] [green]{value}[/green]")
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, (dict, list)):
                        child = parent.add("•")
                        add_nodes(child, item)
                    else:
                        parent.add(f"• [green]{item}[/green]")

        add_nodes(tree, data)
        self.console.print(tree)

    def print_markdown(self, content: str) -> None:
        """Print markdown content."""
        md = Markdown(content, code_theme="monokai")
        self.console.print(md)

    def print_code(
        self,
        code: str,
        language: str = "python",
        title: Optional[str] = None
    ) -> None:
        """Print syntax-highlighted code."""
        syntax = Syntax(code, language, theme="monokai", line_numbers=True)
        self.console.print(Panel(syntax, title=title or "Code"))

    def clear(self) -> None:
        """Clear terminal."""
        self.console.clear()

    def print_divider(self, char: str = "─", style: str = "dim") -> None:
        """Print divider line."""
        self.console.print(f"[{style}]{char * self.console.width}[/{style}]")

    def print_header(
        self,
        text: str,
        level: int = 1,
        style: str = "green"
    ) -> None:
        """Print header."""
        if level == 1:
            self.console.print(f"[bold {style}]{text}[/bold {style}]")
        else:
            self.console.print(f"[{style}]{text}[/{style}]")

    def print_error(self, message: str) -> None:
        """Print error message."""
        self.console.print(f"[bold red]Error:[/bold red] {message}")

    def print_warning(self, message: str) -> None:
        """Print warning message."""
        self.console.print(f"[bold yellow]Warning:[/bold yellow] {message}")

    def print_success(self, message: str) -> None:
        """Print success message."""
        self.console.print(f"[bold green]Success:[/bold green] {message}")

    def print_info(self, message: str) -> None:
        """Print info message."""
        self.console.print(f"[cyan]Info:[/cyan] {message}")

    def get_input(self, prompt: str = "> ") -> str:
        """Get user input."""
        return self.console.input(f"[bold green]PHANTOM[/bold green] {prompt}")


def create_help_table() -> Table:
    """Create help command table."""
    commands = [
        ("/search", "Search the web"),
        ("/read", "Read a URL"),
        ("/crawl", "Crawl a website"),
        ("/browse", "Interactive browser"),
        ("/headers", "Analyze security headers"),
        ("/decode", "Auto-detect and decode"),
        ("/encode", "Encode data"),
        ("/hash", "Generate hashes"),
        ("/cve", "Lookup CVE details"),
        ("/think", "Set thinking mode"),
        ("/learn", "Learn from URL/topic"),
        ("/evolve", "Run evolution cycle"),
        ("/kb", "Knowledge base commands"),
        ("/model", "LLM model commands"),
        ("/session", "Session management"),
        ("/theme", "Switch theme"),
        ("/stats", "Show statistics"),
        ("/history", "Search conversation history"),
        ("/export", "Export data"),
        ("/clear", "Clear terminal"),
        ("/help", "Show this help"),
        ("/quit", "Exit PHANTOM"),
    ]

    table = Table(title="Available Commands")
    table.add_column("Command", style="cyan")
    table.add_column("Description", style="green")

    for cmd, desc in commands:
        table.add_row(cmd, desc)

    return table