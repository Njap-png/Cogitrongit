"""Splash - Terminal splash screens."""

import uuid
from typing import Dict, Any, Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.align import Align

from core.config import Config, detect_platform


ASCII_LOGO = r"""
 ██████╗ ██╗  ██╗ █████╗ ███╗   ██╗████████╗ ██████╗ ███╗   ███╗
 ██╔══██╗██║  ██║██╔══██╗████╗  ██║╚══██╔══╝██╔═══██╗████╗ ████║
 ██████╔╝███████║███████║██╔██╗ ██║   ██║   ██║   ██║██╔████╔██║
 ██╔═══╝ ██╔══██║██╔══██║██║╚██╗██║   ██║   ██║   ██║██║╚██╔╝██║
 ██║     ██║  ██║██║  ██║██║ ╚████║   ██║   ╚██████╔╝██║ ╚═╝ ██║
 ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝    ╚═════╝ ╚═╝     ╚═╝
"""


MINI_LOGO = r"""
 ██████╗ ██╗  ██╗ █████╗ ███╗   ██╗████████╗ ██████╗ ███╗   ███╗
 ██╔══██╗██║  ██║██╔══██╗████╗  ██║╚══██╔══╝██╔═══██╗████╗ ████║
 ██████╔╝███████║███████║██╔██╗ ██║   ██║   ██║   ██║██╔████╔██║
 ██╔═══╝ ██╔══██║██╔══██║██║╚██╗██║   ██║   ██║   ██║██║╚██╔╝██║
 ██║     ██║  ██║██║  ██║██║ ╚████║   ██║   ╚██████╔╝██║ ╚═╝ ██║
 ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝    ╚═════╝ ╚═╝     ╚═╝
"""


class Splash:
    """Terminal splash screen."""

    def __init__(self, config: Optional[Config] = None):
        """Initialize splash."""
        self.config = config or Config.get_instance()
        self.console = Console()
        self.platform = detect_platform()

    def render(
        self,
        backend: str = "unknown",
        model: str = "unknown",
        search_engine: str = "duckduckgo",
        kb_count: int = 0,
        evolution_count: int = 0,
    ) -> None:
        """Render full splash screen."""
        self.console.clear()

        session_id = str(uuid.uuid4())[:8]

        engine_count = 5

        self.console.print()
        self.console.print(f"[bold green]{ASCII_LOGO}[/bold green]")

        self.console.print(
            Align(
                Panel(
                    "[ Polymorphic Heuristic AI · Network Threat Analysis · Mentoring ]",
                    title="[ v2.0.0-OMEGA ]",
                    border_style="green",
                ),
                align="center",
            )
        )

        self.console.print()
        self.console.print(f'[dim]"What you can\'t see can still compromise you."[/dim]')
        self.console.print()

        table = Table(box=None, show_header=False, padding=1)
        table.add_column("label", style="cyan")
        table.add_column("status", style="green")
        table.add_column("detail", style="dim")

        table.add_row(
            "◈ Thinking Engines",
            "██████████",
            f"{engine_count} ACTIVE (Chain · Parallel · Adversarial · Meta · Devil)"
        )
        table.add_row(
            "◈ LLM Backend",
            "██████████",
            f"{backend} / {model}"
        )
        table.add_row(
            "◈ Web Search",
            "██████████",
            f"READY ({search_engine})"
        )
        table.add_row("◈ Web Crawler", "██████████", "READY")
        table.add_row("◈ Web Viewer", "██████████", "READY")
        table.add_row(
            "◈ Knowledge Base",
            "██████████",
            f"{kb_count} entries"
        )
        table.add_row(
            "◈ Self-Evolution",
            "██████████",
            f"ACTIVE — cycle #{evolution_count}"
        )
        table.add_row(
            "◈ Session",
            "██████████",
            session_id
        )
        table.add_row(
            "◈ Platform",
            "██████████",
            self.platform.upper()
        )

        self.console.print(table)

        self.console.print()
        self.console.print("[dim]─" * 60)
        self.console.print("[bold green]Type your question or /help to see all commands. PHANTOM is ready.[/bold green]")
        self.console.print("[dim]─" * 60)
        self.console.print()

    def render_mini(
        self,
        engines: int = 5,
        kb_entries: int = 0
    ) -> None:
        """Render mini splash."""
        self.console.print()
        self.console.print(f"[bold green]{MINI_LOGO}[/bold green]")
        self.console.print()
        self.console.print(
            f"[dim]PHANTOM OMEGA-CORE ─── v2.0.0 ─── "
            f"{engines} engines active ─── {kb_entries} KB entries[/dim]"
        )
        self.console.print()


class MiniSplash(Splash):
    """Mini splash for /clear command."""

    def render(self) -> None:
        """Render mini splash."""
        super().render_mini()