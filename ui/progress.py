"""Progress - Progress bars, spinners, status."""

from typing import Optional, List, Dict, Any
from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TimeRemainingColumn,
    TaskProgressColumn,
    TimeElapsedColumn,
)
from rich.spinner import Spinner
from rich.table import Table
from rich.panel import Panel

from core.config import Config


class ProgressDisplay:
    """Progress and status display utilities."""

    def __init__(self, config: Optional[Config] = None):
        """Initialize progress display."""
        self.config = config or Config.get_instance()
        self.console = Console()
        self._progress: Optional[Progress] = None

    def create_progress(self) -> Progress:
        """Create progress bar manager."""
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=self.console,
        )
        self._progress = progress
        return progress

    def thinking_progress(self) -> Dict[str, Any]:
        """Create thinking engine progress display."""
        return {
            "chain": {"done": False, "time": 0.0},
            "parallel": {"done": False, "time": 0.0},
            "devil": {"done": False, "time": 0.0},
            "meta": {"done": False, "time": 0.0},
            "redteam": {"done": False, "time": 0.0},
            "synthesis": {"done": False, "time": 0.0},
        }

    def render_thinking_bar(
        self,
        engines: Dict[str, Dict[str, Any]],
        total_time: float
    ) -> None:
        """Render thinking engine progress bar."""
        table = Table(
            title="◈ PHANTOM MULTI-ENGINE THINKING",
            box=None,
            show_header=False,
        )

        table.add_column("Engine", style="cyan")
        table.add_column("Status", width=10)
        table.add_column("Time", width=6)

        for engine_name, data in engines.items():
            status = "✓" if data["done"] else "..."
            time_str = f"{data['time']:.1f}s"
            table.add_row(
                engine_name.upper(),
                status,
                time_str if data["done"] else "-"
            )

        self.console.print()
        self.console.print(Panel(table, border_style="green"))
        self.console.print(f"[dim]Total: {total_time:.1f}s[/dim]")

    def status_spinner(self, message: str) -> Spinner:
        """Create status spinner."""
        return Spinner("dots", text=message)

    def render_stats(
        self,
        stats: Dict[str, Any],
        title: str = "Statistics"
    ) -> None:
        """Render statistics panel."""
        lines = []
        for key, value in stats.items():
            lines.append(f"**{key}:** {value}")

        self.console.print(Panel("\n".join(lines), title=title))

    def render_loading_bar(
        self,
        current: int,
        total: int,
        label: str = "Loading"
    ) -> None:
        """Render loading progress bar."""
        percentage = (current / total * 100) if total > 0 else 0
        bar = "█" * int(percentage / 5) + "░" * (20 - int(percentage / 5))

        self.console.print(
            f"\r{label}: [{bar}] {percentage:.0f}%",
            end="" if current < total else "\n"
        )


def create_status_table(items: List[Dict[str, Any]]) -> Table:
    """Create status table."""
    table = Table(show_header=True)
    table.add_column("Status", style="green")
    table.add_column("Component")

    for item in items:
        table.add_row(item.get("status", "●"), item.get("name", ""))

    return table