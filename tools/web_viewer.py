"""Web Viewer - Terminal web page renderer."""

import logging
import re
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import markdownify
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree
from rich.markdown import Markdown

from tools.web_crawler import WebCrawler, PageContent

logger = logging.getLogger("phantom.webviewer")


class WebViewer:
    """Render web content beautifully in terminal."""

    def __init__(self, crawler: Optional[WebCrawler] = None):
        """Initialize web viewer."""
        self.crawler = crawler or WebCrawler()
        self.console = Console()

    def render(self, url_or_content: str) -> None:
        """Render URL or content to terminal."""
        if url_or_content.startswith(("http://", "https://")):
            page = self.crawler.fetch_page(url_or_content)
            if page:
                self._render_page(page)
            else:
                self.console.print(
                    "[red]Failed to fetch page[/red]"
                )
        else:
            self._render_text(url_or_content)

    def _render_page(self, page: PageContent) -> None:
        """Render a page to terminal."""
        self.console.print()
        self.console.print(
            Panel(
                f"[bold cyan]{page.title}[/bold cyan]\n"
                f"[dim]{page.url}[/dim]\n"
                f"[dim]Words: {page.word_count} | "
                f"Fetched: {page.fetched_at[:10]}[/dim]",
                title="Page Info",
                border_style="green"
            )
        )

        markdown = self._html_to_markdown(page.html)

        self.console.print()
        try:
            md = Markdown(markdown, code_theme="monokai")
            self.console.print(md)
        except Exception:
            self.console.print(page.text[:3000])

    def _render_text(self, text: str) -> None:
        """Render plain text to terminal."""
        self.console.print()
        self.console.print(
            Panel(
                text[:5000],
                title="Content",
                border_style="green"
            )
        )

    def _html_to_markdown(self, html: str) -> str:
        """Convert HTML to Markdown."""
        try:
            md = markdownify.Markdownify().convert(html)
            return md
        except Exception:
            return html

    def render_links(
        self,
        links: List[str],
        base_url: str
    ) -> Optional[str]:
        """Show links as numbered table."""
        if not links:
            return None

        table = Table(title="Links Found")
        table.add_column("#", style="cyan", width=3)
        table.add_column("URL", style="blue")
        table.add_column("Type", style="dim")

        link_data = []
        for i, link in enumerate(links[:50], 1):
            link_type = "external"
            if link.startswith(base_url):
                link_type = "internal"
            elif "." not in Path(link).suffix:
                link_type = "page"

            table.add_row(str(i), link[:80], link_type)
            link_data.append(link)

        self.console.print()
        self.console.print(table)

        return link_data[0] if link_data else None

    def render_security_headers(self, headers: Dict[str, Any]) -> None:
        """Render security headers."""
        table = Table(title="Security Headers")
        table.add_column("Header", style="cyan")
        table.add_column("Value", style="blue")
        table.add_column("Status", style="bold")
        table.add_column("Recommendation", style="dim")

        for name, header in headers.items():
            if hasattr(header, "status"):
                status_style = "green"
                if header.status == "MISSING":
                    status_style = "red"
                elif header.status == "MISCONFIGURED":
                    status_style = "yellow"

                table.add_row(
                    header.name,
                    header.value[:50] + "..." if len(header.value) > 50 else header.value,
                    f"[{status_style}]{header.status}[/{status_style}]",
                    header.recommendation
                )
            else:
                table.add_row(name, str(header)[:50], "UNKNOWN", "")

        self.console.print()
        self.console.print(table)

    def render_sitemap(self, sitemap: Any) -> None:
        """Render site map as tree."""
        self.console.print()
        self.console.print(
            f"[bold]Site Map:[/bold] {sitemap.start_url}"
        )
        self.console.print(
            f"[dim]Pages: {len(sitemap.pages)} | "
            f"Links: {sitemap.total_links} | "
            f"Time: {sitemap.crawl_time:.1f}s[/dim]"
        )

        tree = Tree("[bold green]Pages[/bold green]")

        for page in sitemap.pages[:30]:
            status_icon = "✓" if page.get("status") == 200 else "✗"
            url_short = page["url"].replace(
                sitemap.start_url, ""
            ) or "/"
            if len(url_short) > 50:
                url_short = url_short[:50] + "..."

            tree.add(
                f"{status_icon} [{page.get('depth', 0)}]"
                f"[blue]{url_short}[/blue]"
                f" [dim]({page.get('status')})[/dim]"
            )

        self.console.print()
        self.console.print(tree)

        if sitemap.errors:
            self.console.print()
            self.console.print(
                f"[yellow]Errors: {len(sitemap.errors)}[/yellow]"
            )

    def save_as_markdown(self, url: str, output_path: str) -> str:
        """Fetch page and save as Markdown."""
        page = self.crawler.fetch_page(url)
        if not page:
            return ""

        markdown = self._html_to_markdown(page.html)

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w") as f:
            f.write(f"# {page.title}\n\n")
            f.write(f"Source: {url}\n\n")
            f.write("---\n\n")
            f.write(markdown)

        return str(output_file)

    def browse(self, start_url: str) -> None:
        """Interactive terminal browser."""
        current_url = start_url
        history: List[str] = [start_url]

        while True:
            self.console.print()
            self.console.print(
                f"[bold cyan]Browsing:[/bold cyan] {current_url}"
            )

            page = self.crawler.fetch_page(current_url)
            if not page:
                self.console.print("[red]Failed to load page[/red]")
                break

            self.console.print()
            self.console.print(
                f"[bold]{page.title}[/bold]"
            )
            self.console.print(
                f"[dim]{len(page.text)} characters[/dim]"
            )

            if page.links:
                self.console.print()
                self.console.print(
                    f"[yellow]{len(page.links)} links found[/yellow]"
                )
                self.render_links(page.links, current_url)

            self.console.print()
            user_input = self.console.input(
                "[bold green]PHANTOM[/bold green] "
                "[dim](n=next link, b=back, q=quit)[/dim]: "
            )

            cmd = user_input.strip().lower()

            if cmd == "q":
                break
            elif cmd == "b" and len(history) > 1:
                history.pop()
                current_url = history[-1]
            elif cmd.isdigit() and page.links:
                idx = int(cmd) - 1
                if 0 <= idx < len(page.links):
                    current_url = page.links[idx]
                    history.append(current_url)
            elif cmd.startswith("s "):
                filename = cmd[2:].strip()
                if filename:
                    self.save_as_markdown(current_url, filename)
                    self.console.print(
                        f"[green]Saved to {filename}[/green]"
                    )