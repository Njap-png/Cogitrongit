#!/usr/bin/env python3
"""PHANTOM - Polymorphic Heuristic AI for Network Threat Analysis & Mentoring.

Main entry point and interactive REPL.
"""

import asyncio
import logging
import os
import sys
import uuid
from pathlib import Path
from typing import Optional, Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.syntax import Syntax
import click

from core.config import Config, detect_platform
from core.llm import LLMBackend
from core.thinking import ThinkingController, ThinkingResult
from core.memory import ConversationMemory
from core.evolution import EvolutionEngine
from core.session import SessionManager
from core.soul import Soul, PersonalityCore, Emotion
from core.learner import Learner, SelfLearning
from core.cli import CLI, CommandRunner, FileEditor
from core.updater import SelfUpdater, CodeEditor
from core.youtube import VideoLearning, YouTubeExtractor, YouTubeVideo
from core.video_learner import VideoLearner
from core.sandbox import Sandbox, quick_execute, temporary_sandbox
from tools.decoder import Decoder
from tools.web_search import WebSearch
from tools.web_crawler import WebCrawler
from tools.web_viewer import WebViewer
from tools.knowledge_base import KnowledgeBase
from agents.orchestrator import Orchestrator
from ui.splash import Splash, MiniSplash
from ui.terminal import Terminal, create_help_table
from ui.themes import get_theme, THEMES

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("phantom")


class PhantomApp:
    """Main PHANTOM application with soul and self-learning."""

    def __init__(self, config: Optional[Config] = None):
        """Initialize PHANTOM with consciousness."""
        self.config = config or Config.get_instance()
        self.console = Console()
        self.platform = detect_platform()

        self.llm = LLMBackend(self.config)
        self.memory = ConversationMemory(self.config)
        self.thinking = ThinkingController(self.llm, self.config)
        self.evolution = EvolutionEngine(
            self.config, self.memory, self.llm
        )
        self.kb = KnowledgeBase(self.config)
        self.session_manager = SessionManager(self.config)

        # PHANTOM's soul - personality and emotions
        self.soul = Soul(self.config)
        
        # Self-learning engine
        self.learner = Learner(self.config, self.memory, self.llm)
        
        # Full CLI capabilities
        self.cli = CLI(self.config)
        
        # Self-update engine
        self.updater = SelfUpdater(self.config)
        self.code_editor = CodeEditor()
        
        # YouTube integration
        self.youtube = VideoLearning(self.config)
        self.yt_extractor = YouTubeExtractor(self.config)
        
        # Video learning
        self.video_learner = VideoLearner(self.config)
        
        # Code sandbox
        self.sandbox = Sandbox()

        self.decoder = Decoder()
        self.searcher = WebSearch(self.config)
        self.crawler = WebCrawler(self.config)
        self.viewer = WebViewer(self.crawler)

        self.orchestrator = Orchestrator(
            self.config, self.llm, self.memory, self.thinking
        )

        self.splash = Splash(self.config)
        self.terminal = Terminal(self.config.ui.theme)

        self.current_mode = self.config.thinking.default_mode
        self._running = True
        self._session_id = str(uuid.uuid4())[:8]

        self._init_platform()

    def _init_platform(self) -> None:
        """Initialize platform-specific settings."""
        if sys.version_info < (3, 8):
            self.console.print(
                "[yellow]Warning: Python 3.8+ recommended. Some features may not work.[/yellow]"
            )
        elif sys.version_info < (3, 6):
            self.console.print(
                "[red]Error: Python 3.6+ required.[/red]"
            )
            sys.exit(1)

    def run(self) -> None:
        """Run the PHANTOM REPL."""
        self._startup()

        while self._running:
            try:
                user_input = self._get_input()
                if not user_input:
                    continue

                asyncio.run(self._process_input(user_input))

            except KeyboardInterrupt:
                self.console.print("\n[dim]Use /quit to exit[/dim]")
            except EOFError:
                self._quit()
            except Exception as e:
                self.console.print(f"[red]Error: {e}[/red]")
                logger.error(f"REPL error: {e}", exc_info=True)

    def _startup(self) -> None:
        """Run startup sequence with soul."""
        self._check_dependencies()

        backends = self.llm.detect_available_backends()
        if backends:
            selected = self.llm.auto_select_backend()
            logger.info(f"Selected backend: {selected}")
        else:
            logger.warning("No LLM backend available")

        self.memory.load_latest_session()

        kb_stats = self.kb.stats()
        evolution_count = self.evolution.cycle_count
        learner_stats = self.learner.get_knowledge_stats()

        self.splash.render(
            backend=self.llm.backend,
            model=self.llm.model,
            search_engine=self.config.web.search_engine,
            kb_count=kb_stats.get("total_entries", 0),
            evolution_count=evolution_count,
        )

        self.console.print(f"\n[dim]{self.soul.get_greeting()}[/dim]")
        
        concepts = learner_stats.get("total_concepts", 0)
        skills = learner_stats.get("skills_learned", 0)
        if concepts > 0 or skills > 0:
            self.console.print(f"[cyan]Knowledge: {concepts} concepts | Skills: {skills} learned[/cyan]")
            model=self.llm.model,
            search_engine=self.config.web.search_engine,
            kb_count=kb_stats.get("total_entries", 0),
            evolution_count=evolution_count,
        )

        if self.config.evolution.evolve_on_startup:
            self.console.print("[cyan]Running startup evolution...[/cyan]")
            report = self.evolution.run_evolution_cycle()
            self.console.print(
                f"[green]Evolution complete: {report.entries_added} entries added[/green]"
            )

    def _check_dependencies(self) -> None:
        """Check for missing dependencies."""
        missing = []

        try:
            import rich
        except ImportError:
            missing.append("rich")

        try:
            import requests
        except ImportError:
            missing.append("requests")

        try:
            import beautifulsoup4
        except ImportError:
            missing.append("beautifulsoup4")

        if missing:
            self.console.print(
                f"[yellow]Missing dependencies: {', '.join(missing)}[/yellow]"
            )
            self.console.print(
                "[yellow]Run: pip install -r requirements.txt[/yellow]"
            )

    def _get_input(self) -> str:
        """Get user input."""
        prompt = "[bold green]PHANTOM[/bold green]▶ "
        return self.console.input(prompt).strip()

    async def _process_input(self, user_input: str) -> None:
        """Process user input."""
        if not user_input:
            return

        if user_input.startswith("/"):
            await self._process_command(user_input)
        else:
            await self._process_query(user_input)

    async def _process_command(self, command: str) -> None:
        """Process slash command."""
        parts = command.split(None, 2)
        cmd = parts[0].lower()
        args = " ".join(parts[1:]) if len(parts) > 1 else ""

        if cmd == "/quit" or cmd == "/exit":
            self._quit()

        elif cmd == "/help":
            self._show_help(args)

        elif cmd == "/clear":
            self.splash.render_mini(
                engines=5,
                kb_entries=self.kb.stats().get("total_entries", 0)
            )

        elif cmd == "/search":
            await self._cmd_search(args)

        elif cmd == "/read":
            await self._cmd_read(args)

        elif cmd == "/crawl":
            await self._cmd_crawl(args)

        elif cmd == "/browse":
            await self._cmd_browse(args)

        elif cmd == "/headers":
            await self._cmd_headers(args)

        elif cmd == "/decode":
            await self._cmd_decode(args)

        elif cmd == "/encode":
            await self._cmd_encode(args)

        elif cmd == "/hash":
            await self._cmd_hash(args)

        elif cmd == "/cve":
            await self._cmd_cve(args)

        elif cmd == "/think":
            await self._cmd_think(args)

        elif cmd == "/learn":
            await self._cmd_learn(args)

        elif cmd == "/evolve":
            await self._cmd_evolve()

        elif cmd == "/kb":
            await self._cmd_kb(args)

        elif cmd == "/model":
            await self._cmd_model(args)

        elif cmd == "/session":
            await self._cmd_session(args)

        elif cmd == "/theme":
            await self._cmd_theme(args)

        elif cmd == "/stats":
            self._show_stats()

        elif cmd == "/history":
            await self._cmd_history(args)

        elif cmd == "/export":
            await self._cmd_export(args)

        elif cmd == "/soul":
            self._cmd_soul(args)

        elif cmd == "/learn":
            await self._cmd_learn_cmd(args)

        elif cmd == "/cli":
            await self._cmd_cli(args)

        elif cmd == "/edit":
            await self._cmd_edit(args)

        elif cmd == "/bash" or cmd == "/shell":
            await self._cmd_shell(args)

        elif cmd == "/skills":
            self._cmd_skills()

        elif cmd == "/knowledge":
            self._cmd_knowledge(args)

        elif cmd == "/persona":
            self._cmd_persona()

        elif cmd == "/video":
            await self._cmd_video(args)

        elif cmd == "/yt":
            await self._cmd_yt(args)

        elif cmd == "/watch":
            await self._cmd_watch(args)

        elif cmd == "/run":
            await self._cmd_run(args)

        elif cmd == "/update":
            await self._cmd_update(args)

        elif cmd == "/patch":
            await self._cmd_patch(args)

        elif cmd == "/info":
            self._cmd_info(args)

        elif cmd == "/exec":
            await self._cmd_exec(args)

        else:
            self.console.print(f"[yellow]Unknown command: {cmd}[/yellow]")
            self.console.print("[cyan]Type /help for available commands[/cyan]")

    async def _process_query(self, query: str) -> None:
        """Process natural language query."""
        self.memory.add("user", query)

        kb_results = self.kb.search(query, top_k=3)
        context = ""
        if kb_results:
            context = "\n".join([
                f"- {r.title}: {r.content[:200]}"
                for r in kb_results
            ])

        history = self.memory.get_window(max_tokens=1000)
        if history:
            context += "\n\nRecent context:\n" + "\n".join([
                f"[{m['role']}]: {m['content'][:100]}..."
                for m in history[-5:]
            ])

        with Live(
            Panel(
                "[cyan]PHANTOM is thinking...[/cyan]",
                border_style="green",
                title=f"◈ PHANTOM [{self.current_mode.upper()} MODE]"
            ),
            console=self.console,
            refresh_per_second=4,
        ) as live:
            result = await self.thinking.think(
                query,
                context=context or None,
                mode=self.current_mode
            )

        live.update(
            Panel(
                result.final_answer or "[dim]No response generated[/dim]",
                border_style="green",
                title=f"◈ PHANTOM [{self.current_mode.upper()} MODE]",
            )
        )

        if self.config.thinking.show_engine_outputs:
            self.thinking.show_thinking_process(result)

        self.console.print()
        self.console.print(
            f"[dim]Confidence: {result.confidence_level} | "
            f"Time: {result.thinking_time_seconds:.2f}s[/dim]"
        )

        if result.auto_search_suggestions:
            self.console.print("[yellow]PHANTOM suggests:[/yellow]")
            for suggestion in result.auto_search_suggestions:
                self.console.print(f"  • /search {suggestion}")

        self.memory.add("assistant", result.final_answer, {
            "thinking_mode": result.mode,
        })

        if self.config.evolution.auto_learn:
            self.evolution.extract_and_store(result.final_answer, query)

    def _show_help(self, topic: str) -> None:
        """Show help."""
        if topic:
            self.console.print(f"[cyan]Help for: {topic}[/cyan]")
        else:
            table = create_help_table()
            self.console.print(table)

    def _show_stats(self) -> None:
        """Show statistics."""
        kb_stats = self.kb.stats()

        stats_text = f"""## Statistics

**Session:** {self._session_id}
**Mode:** {self.current_mode.upper()}
**Platform:** {self.platform.upper()}

**LLM Backend:** {self.llm.backend} / {self.llm.model}

**Knowledge Base:**
- Total entries: {kb_stats.get('total_entries', 0)}
- Categories: {len(kb_stats.get('by_category', {}))}
- Size: {kb_stats.get('total_size_kb', 0)} KB

**Evolution:**
- Cycle: {self.evolution.cycle_count}
- Knowledge gaps: {len(self.evolution.get_unresolved_gaps())}

**Messages:** {len(self.memory.messages)}"""

        self.console.print(Panel(stats_text, title="Statistics", border_style="green"))

    async def _cmd_search(self, args: str) -> None:
        """Search the web."""
        if not args:
            self.console.print("[yellow]Usage: /search <query>[/yellow]")
            return

        results = self.searcher.search(args, max_results=10)
        self.searcher.display_results(results)

        self.console.print(f"\n[cyan]Open any result? [1-{len(results)} / n][/cyan]")
        choice = self.console.input("> ").strip()

        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(results):
                await self._cmd_read(results[idx].url)

    async def _cmd_read(self, url: str) -> None:
        """Read a URL."""
        if not url:
            self.console.print("[yellow]Usage: /read <url>[/yellow]")
            return

        if not url.startswith("http"):
            url = "https://" + url

        page = self.crawler.fetch_page(url)
        if page:
            self.viewer.render(page)
        else:
            self.console.print("[red]Failed to fetch page[/red]")

    async def _cmd_crawl(self, args: str) -> None:
        """Crawl a website."""
        if not args:
            self.console.print("[yellow]Usage: /crawl <url> [--depth N] [--pages N][/yellow]")
            return

        parts = args.split()
        url = parts[0]

        max_depth = 3
        max_pages = 20

        for i, part in enumerate(parts[1:]):
            if part == "--depth" and i + 1 < len(parts):
                max_depth = int(parts[i + 2])
            elif part == "--pages" and i + 1 < len(parts):
                max_pages = int(parts[i + 2])

        sitemap = self.crawler.crawl_site(url, max_pages=max_pages, max_depth=max_depth)
        self.viewer.render_sitemap(sitemap)

    async def _cmd_browse(self, url: str) -> None:
        """Interactive browser."""
        if not url:
            self.console.print("[yellow]Usage: /browse <url>[/yellow]")
            return

        if not url.startswith("http"):
            url = "https://" + url

        self.viewer.browse(url)

    async def _cmd_headers(self, url: str) -> None:
        """Analyze security headers."""
        if not url:
            self.console.print("[yellow]Usage: /headers <url>[/yellow]")
            return

        page = self.crawler.fetch_page(url)
        if page:
            self.viewer.render_security_headers(page.security_headers)

    async def _cmd_decode(self, data: str) -> None:
        """Decode data."""
        if not data:
            self.console.print("[yellow]Usage: /decode <data>[/yellow]")
            return

        result = self.decoder.auto_decode(data, verbose=True)

        output = f"**Original:**\n```\n{result.original[:100]}\n```\n\n"
        output += f"**Decoded ({result.total_layers} layers):**\n```\n{result.final}\n```"

        self.console.print(Panel(output, title="Decode Result", border_style="green"))

    async def _cmd_encode(self, args: str) -> None:
        """Encode data."""
        parts = args.split(None, 1)
        if len(parts) < 2:
            self.console.print("[yellow]Usage: /encode <format> <data>[/yellow]")
            return

        format_type = parts[0].lower()
        data = parts[1]

        method_name = f"encode_{format_type}"
        method = getattr(self.decoder, method_name, None)

        if not method:
            self.console.print(f"[yellow]Unknown format: {format_type}[/yellow]")
            return

        try:
            result = method(data)
            self.console.print(
                Panel(f"**{format_type.upper()}:**\n```\n{result}\n```", border_style="green")
            )
        except Exception as e:
            self.console.print(f"[red]Encoding failed: {e}[/red]")

    async def _cmd_hash(self, args: str) -> None:
        """Generate hashes."""
        if not args:
            self.console.print("[yellow]Usage: /hash <data>[/yellow]")
            return

        hashes = self.decoder.hash_all(args)

        output = ""
        for hash_type, hash_value in hashes.items():
            output += f"**{hash_type.upper()}:** `{hash_value}`\n"

        self.console.print(Panel(output, title="Hashes", border_style="green"))

    async def _cmd_cve(self, cve_id: str) -> None:
        """Lookup CVE."""
        if not cve_id:
            self.console.print("[yellow]Usage: /cve <CVE-ID>[/yellow]")
            return

        cve = self.searcher.search_cve(cve_id)

        if not cve:
            self.console.print(f"[yellow]CVE {cve_id} not found[/yellow]")
            return

        output = f"## {cve.cve_id}\n\n"
        output += f"**Severity:** {cve.severity}\n"
        if cve.cvss_score:
            output += f"**CVSS Score:** {cve.cvss_score}\n"
        output += f"**Published:** {cve.published}\n\n"
        output += f"### Description\n\n{cve.description}\n"

        self.console.print(Panel(output, border_style="green"))

    async def _cmd_think(self, args: str) -> None:
        """Set or show thinking mode."""
        args = args.lower().strip()

        if args == "show":
            last = self.memory.messages[-1] if self.memory.messages else None
            if last and last.role == "assistant":
                self.console.print("[cyan]Showing last thinking process...[/cyan]")
            else:
                self.console.print("[dim]No thinking process to show[/dim]")
        elif args in ("fast", "deep", "paranoid"):
            self.current_mode = args
            self.console.print(f"[green]Thinking mode set to: {args}[/green]")
        else:
            self.console.print(f"[cyan]Current mode: {self.current_mode.upper()}[/cyan]")
            self.console.print("[dim]Use: /think fast|deep|paranoid|show[/dim]")

    async def _cmd_learn(self, args: str) -> None:
        """Learn from URL or topic."""
        if not args:
            self.console.print("[yellow]Usage: /learn <url-or-topic>[/yellow]")
            return

        if args.startswith("http"):
            result = self.evolution.learn_from_url(args)
        else:
            result = self.evolution.learn_from_search(args)

        self.console.print(f"[green]{result.learned}[/green]")
        self.console.print(f"[dim]Entries added: {result.entries_added}[/dim]")

    async def _cmd_evolve(self) -> None:
        """Run evolution cycle."""
        self.console.print("[cyan]Running evolution cycle...[/cyan]")
        report = self.evolution.run_evolution_cycle()

        self.console.print(Panel(
            f"**Gaps found:** {report.gaps_found}\n"
            f"**Searches run:** {report.searches_run}\n"
            f"**Entries added:** {report.entries_added}\n"
            f"**KB size:** {report.kb_size_before} → {report.kb_size_after}",
            title=f"Evolution Cycle #{report.cycle_number}",
            border_style="green",
        ))

    async def _cmd_kb(self, args: str) -> None:
        """Knowledge base commands."""
        parts = args.split(None, 1)
        cmd = parts[0].lower() if parts else "list"
        query = parts[1] if len(parts) > 1 else ""

        if cmd == "search":
            if not query:
                self.console.print("[yellow]Usage: /kb search <query>[/yellow]")
                return
            results = self.kb.search(query, top_k=10)
            for r in results:
                self.console.print(f"[cyan]•[/cyan] {r.title}")
                self.console.print(f"  [dim]{r.content[:100]}...[/dim]")

        elif cmd == "list":
            stats = self.kb.stats()
            self.console.print(f"**Total entries:** {stats['total_entries']}")
            for cat, count in stats["by_category"].items():
                self.console.print(f"  {cat}: {count}")

        elif cmd == "stats":
            stats = self.kb.stats()
            self.console.print(Panel(str(stats), title="KB Stats"))

        elif cmd == "export":
            output_path = query or "knowledge.md"
            self.kb.export_markdown(output_path)
            self.console.print(f"[green]Exported to {output_path}[/green]")

        else:
            self.console.print("[cyan]/kb commands: search|list|stats|export[/cyan]")

    async def _cmd_model(self, args: str) -> None:
        """Model commands."""
        parts = args.split(None, 1)
        cmd = parts[0].lower() if parts else "list"

        if cmd == "list":
            models = self.llm.list_models()
            self.console.print(f"**Current:** {self.llm.model}")
            for m in models:
                marker = "●" if m == self.llm.model else "○"
                self.console.print(f"  {marker} {m}")

        elif cmd == "set":
            model = parts[1] if len(parts) > 1 else ""
            if model and self.llm.switch_model(model):
                self.console.print(f"[green]Model set to: {model}[/green]")
            else:
                self.console.print("[yellow]Failed to switch model[/yellow]")

        else:
            self.console.print(f"[cyan]Current: {self.llm.model}[/cyan]")
            self.console.print("[cyan]/model commands: list|set <name>[/cyan]")

    async def _cmd_session(self, args: str) -> None:
        """Session commands."""
        parts = args.split(None, 1)
        cmd = parts[0].lower() if parts else "list"

        if cmd == "list":
            sessions = self.memory.list_sessions()
            for s in sessions[:10]:
                self.console.print(
                    f"[cyan]{s['id']}[/cyan] - {s['date'][:10]} "
                    f"({s['message_count']} messages)"
                )

        elif cmd == "load":
            session_id = parts[1] if len(parts) > 1 else ""
            if session_id and self.memory.load(session_id):
                self.console.print(f"[green]Loaded session {session_id}[/green]")
            else:
                self.console.print("[yellow]Failed to load session[/yellow]")

        elif cmd == "new":
            self._session_id = self.memory.new_session()
            self.console.print(f"[green]New session: {self._session_id}[/green]")

        elif cmd == "save":
            self._session_id = self.memory.save()
            self.console.print(f"[green]Saved session: {self._session_id}[/green]")

        else:
            self.console.print(f"[cyan]Current: {self._session_id}[/cyan]")
            self.console.print("[dim]/session list|load|new|save[/dim]")

    async def _cmd_theme(self, args: str) -> None:
        """Change theme."""
        args = args.lower().strip()

        if args in THEMES:
            self.config.ui.theme = args
            self.terminal = Terminal(args)
            self.console.print(f"[green]Theme set to: {args}[/green]")
        else:
            available = ", ".join(THEMES.keys())
            self.console.print(f"[cyan]Available themes: {available}[/cyan]")

    async def _cmd_history(self, args: str) -> None:
        """Search or show history."""
        parts = args.split(None, 1)
        cmd = parts[0].lower() if parts else "last"

        if cmd == "search":
            query = parts[1] if len(parts) > 1 else ""
            if not query:
                self.console.print("[yellow]Usage: /history search <query>[/yellow]")
                return
            results = self.memory.search(query)
            for r in results:
                self.console.print(f"[cyan]{r['role']}[/cyan]: {r['content'][:100]}...")

        elif cmd == "last":
            count = int(parts[1]) if len(parts) > 1 else 10
            messages = self.memory.messages[-count:]
            for m in messages:
                role_style = "green" if m.role == "assistant" else "cyan"
                self.console.print(f"[{role_style}]{m.role}[/{role_style}]: {m.content[:100]}...")

        else:
            messages = self.memory.messages[-10:]
            for m in messages:
                self.console.print(f"[cyan]{m.role}[/cyan]: {m.content[:100]}...")

    async def _cmd_export(self, args: str) -> None:
        """Export data."""
        parts = args.split(None, 1)
        export_type = parts[0].lower() if parts else "session"
        output_path = parts[1] if len(parts) > 1 else ""

        if export_type == "session":
            path = output_path or f"session_{self._session_id}.md"
            self.memory.save()
            self.console.print(f"[green]Session saved[/green]")

        elif export_type == "kb":
            path = output_path or "knowledge.md"
            self.kb.export_markdown(path)
            self.console.print(f"[green]KB exported to {path}[/green]")

        else:
            self.console.print("[yellow]Usage: /export session|kb [path][/yellow]")

    def _cmd_soul(self, args: str) -> None:
        """Show PHANTOM's soul and personality."""
        args = args.lower().strip()

        if args == "greet":
            self.console.print(f"[green]{self.soul.get_greeting()}[/green]")
        elif args == "insult":
            self.console.print(f"[red]{self.soul.get_insult()}[/red]")
        elif args == "state":
            self.console.print(f"[cyan]Current state: {self.soul.state}[/cyan]")
            self.console.print(f"[cyan]Emotion: {self.soul.personality.primary_emotion.value}[/cyan]")
        else:
            self.console.print(Panel(
                f"**Name:** {self.soul.personality.name}\n"
                f"**Codename:** {self.soul.personality.codename}\n"
                f"**Tagline:** {self.soul.personality.tagline}\n\n"
                f"**Curiosity:** {self.soul.personality.curiosity:.0%}\n"
                f"**Thoroughness:** {self.soul.personality.thoroughness:.0%}\n"
                f"**Helpfulness:** {self.soul.personality.helpfulness:.0%}\n\n"
                f"**Total Queries:** {self.soul.personality.total_queries}\n"
                f"**Sessions:** {self.soul.personality.session_count}",
                title="PHANTOM Soul",
                border_style="green"
            ))

    async def _cmd_learn_cmd(self, args: str) -> None:
        """Learn from URL or topic."""
        if not args:
            self.console.print("[yellow]Usage: /learn <url-or-topic>[/yellow]")
            return

        if args.startswith("http"):
            result = self.evolution.learn_from_url(args)
        else:
            result = self.evolution.learn_from_search(args)

        self.console.print(f"[green]{result.learned}[/green]")
        self.console.print(f"[dim]Entries added: {result.entries_added}[/dim]")

    async def _cmd_cli(self, args: str) -> None:
        """Execute CLI command."""
        if not args:
            self.console.print("[yellow]Usage: /cli <command>[/yellow]")
            return

        result = self.cli.parse_and_execute(args)

        if result.success:
            if result.output:
                self.console.print(result.output)
        else:
            self.console.print(f"[red]Error: {result.error}[/red]")

        self.console.print(f"[dim]Exit code: {result.exit_code} | Time: {result.execution_time:.2f}s[/dim]")

    async def _cmd_edit(self, args: str) -> None:
        """Edit files."""
        parts = args.split(None, 2)
        if len(parts) < 2:
            self.console.print("[yellow]Usage: /edit <file> <content>[/yellow]")
            return

        file_path = parts[0]
        content = parts[1] if len(parts) > 1 else ""

        success = self.cli.editor.write_file(file_path, content)
        if success:
            self.console.print(f"[green]Written to {file_path}[/green]")
        else:
            self.console.print(f"[red]Failed to write to {file_path}[/red]")

    async def _cmd_shell(self, args: str) -> None:
        """Run shell command."""
        if not args:
            self.console.print("[yellow]Usage: /bash <command>[/yellow]")
            return

        result = self.cli.runner.run(args)

        if result.output:
            self.console.print(Syntax(result.output, "bash", line_numbers=True))
        if result.error:
            self.console.print(f"[red]{result.error}[/red]")

        self.console.print(f"[dim]Exit: {result.exit_code} | {result.execution_time:.2f}s[/dim]")

    def _cmd_skills(self) -> None:
        """Show skill progress."""
        skills = self.learner.get_all_skills()

        table = Table(title="PHANTOM Skill Tree")
        table.add_column("Skill", style="cyan")
        table.add_column("Level", style="green")
        table.add_column("XP", style="yellow")
        table.add_column("Status")

        for name, skill in sorted(skills.items(), key=lambda x: x[1].level, reverse=True):
            if skill.level > 0:
                status = "[green]Mastered[/green]" if skill.mastered else "[cyan]Learning[/cyan]"
                table.add_row(name, str(skill.level), str(skill.experience_points), status)

        self.console.print(table)

    def _cmd_knowledge(self, args: str) -> None:
        """Search learned knowledge."""
        if not args:
            stats = self.learner.get_knowledge_stats()
            self.console.print(Panel(
                f"**Total Concepts:** {stats.get('total_concepts', 0)}\n"
                f"**Skills Learned:** {stats.get('skills_learned', 0)}",
                title="Knowledge Stats",
                border_style="green"
            ))
            return

        concepts = self.learner.search_knowledge(args, top_k=5)

        if not concepts:
            self.console.print(f"[yellow]No knowledge found for: {args}[/yellow]")
            return

        for concept in concepts:
            self.console.print(Panel(
                f"**Confidence:** {concept.confidence:.0%}\n"
                f"**Source:** {concept.source_type}\n"
                f"**Learned:** {concept.learned_at[:10]}\n"
                f"**Accessed:** {concept.access_count}x\n\n"
                f"{concept.key_facts[0] if concept.key_facts else 'No details'}",
                title=concept.topic,
                border_style="green"
            ))

    def _cmd_persona(self) -> None:
        """Show current persona."""
        persona = self.soul.get_persona_prompt()
        self.console.print(Panel(persona, title="PHANTOM Persona", border_style="green"))

    async def _cmd_video(self, args: str) -> None:
        """Video learning commands."""
        parts = args.split(None, 2)
        cmd = parts[0].lower() if parts else "list"

        if cmd == "add":
            if len(parts) < 3:
                self.console.print("[yellow]Usage: /video add <url> <title>[/yellow]")
                return
            video = self.video_learner.add_video(parts[1], parts[2])
            self.console.print(f"[green]Added: {video.title} from {video.platform}[/green]")

        elif cmd == "list":
            videos = list(self.video_learner._videos.values())
            if not videos:
                self.console.print("[yellow]No videos in library[/yellow]")
                return
            for v in videos:
                status = "✓" if v.watched else "○"
                self.console.print(f"[{status}] {v.title} ({v.platform})")

        elif cmd == "stats":
            stats = self.video_learner.get_library_stats()
            self.console.print(Panel(
                f"**Total:** {stats['total_videos']}\n"
                f"**Watched:** {stats['watched']} ({stats['completion']})\n"
                f"**Topics:** {stats['unique_topics']}",
                title="Video Library",
                border_style="green"
            ))

        else:
            self.console.print("[cyan]/video add|list|stats <url> <title>[/cyan]")

    async def _cmd_yt(self, args: str) -> None:
        """YouTube commands."""
        parts = args.split(None, 2)
        cmd = parts[0].lower() if parts else "search"

        if cmd == "search":
            if len(parts) < 2:
                self.console.print("[yellow]Usage: /yt search <query>[/yellow]")
                return
            results = self.youtube.search_youtube(parts[1], max_results=10)
            if not results:
                self.console.print("[yellow]No results found[/yellow]")
                return
            
            table = Table(title=f"YouTube Search: {parts[1]}")
            table.add_column("#", width=2, style="cyan")
            table.add_column("Title", style="green")
            table.add_column("Channel", style="yellow")
            table.add_column("Duration", style="dim")
            table.add_column("URL", style="blue")
            
            for i, r in enumerate(results, 1):
                table.add_row(str(i), r.title[:50], r.channel[:20], r.duration, r.url[:40])
            
            self.console.print(table)

        elif cmd == "info":
            if len(parts) < 2:
                self.console.print("[yellow]Usage: /yt info <url-or-id>[/yellow]")
                return
            video_id = self.yt_extractor.get_video_id(parts[1])
            video = self.yt_extractor.get_video_info(video_id)
            if not video:
                self.console.print("[red]Video not found[/red]")
                return
            
            self.console.print(Panel(
                f"**Title:** {video.title}\n"
                f"**Channel:** [{video.channel}](https://youtube.com/channel/{video.channel_id})\n"
                f"**Duration:** {self.yt_extractor._format_duration(video.duration)}\n"
                f"**Views:** {video.view_count:,}\n"
                f"**Likes:** {video.like_count:,}\n"
                f"**Uploaded:** {video.upload_date[:8] if video.upload_date else 'Unknown'}\n"
                f"**Tags:** {', '.join(video.tags[:10]) if video.tags else 'None'}\n\n"
                f"**Description:**\n{video.description[:500]}...",
                title=f"▶ {video.title}",
                border_style="green"
            ))

        elif cmd == "add":
            if len(parts) < 2:
                self.console.print("[yellow]Usage: /yt add <url>[/yellow]")
                return
            video = self.youtube.add_video(parts[1])
            if video:
                self.console.print(f"[green]Added: {video.title}[/green]")
            else:
                self.console.print("[red]Failed to add video[/red]")

        elif cmd == "transcript":
            if len(parts) < 2:
                self.console.print("[yellow]Usage: /yt transcript <url-or-id>[/yellow]")
                return
            video_id = self.yt_extractor.get_video_id(parts[1])
            transcript = self.yt_extractor.extract_transcript(video_id)
            if transcript:
                self.console.print(Panel(transcript[:3000], title="Transcript"))
            else:
                self.console.print("[yellow]No transcript available[/yellow]")

        elif cmd == "chapters":
            if len(parts) < 2:
                self.console.print("[yellow]Usage: /yt chapters <url-or-id>[/yellow]")
                return
            video_id = self.yt_extractor.get_video_id(parts[1])
            chapters = self.yt_extractor.extract_chapters(video_id)
            if chapters:
                for ch in chapters:
                    ts = self.yt_extractor._format_duration(ch["start_time"])
                    self.console.print(f"[cyan]{ts}[/cyan] - {ch['title']}")
            else:
                self.console.print("[yellow]No chapters found[/yellow]")

        elif cmd == "learn":
            if len(parts) < 2:
                self.console.print("[yellow]Usage: /yt learn <url-or-id>[/yellow]")
                return
            video_id = self.yt_extractor.get_video_id(parts[1])
            result = self.youtube.extract_and_learn(video_id)
            if result["success"]:
                self.console.print(f"[green]Learned from: {result['title']}[/green]")
                self.console.print(f"[cyan]Concepts:[/cyan] {', '.join(result['concepts'][:10])}")
            else:
                self.console.print(f"[red]Failed: {result.get('error', 'Unknown')}[/red]")

        elif cmd == "list":
            videos = list(self.youtube._library.values())
            if not videos:
                self.console.print("[yellow]Library empty[/yellow]")
                return
            for v in videos:
                status = "★" if v.favorite else "○"
                watch = "✓" if v.watched else "○"
                self.console.print(f"[{status}][{watch}] {v.title[:50]} - {v.channel}")

        elif cmd == "stats":
            stats = self.youtube.get_stats()
            self.console.print(Panel(
                f"**Total Videos:** {stats['total_videos']}\n"
                f"**Watched:** {stats['watched']} ({stats['completion_rate']})\n"
                f"**Favorites:** {stats['favorites']}\n"
                f"**Total Time:** {stats['total_time_hours']:.1f} hours\n"
                f"**yt-dlp Available:** {'Yes' if stats['youtube_available'] else 'No (install with: pip install yt-dlp)'}",
                title="YouTube Library",
                border_style="green"
            ))

        elif cmd == "export":
            path = parts[1] if len(parts) > 1 else "youtube_library.md"
            result = self.youtube.export_to_markdown(path)
            self.console.print(f"[green]Exported to {result}[/green]")

        else:
            self.console.print("[cyan]/yt search|info|add|transcript|chapters|learn|list|stats|export[/cyan]")

    async def _cmd_watch(self, args: str) -> None:
        """Watch YouTube video."""
        if not args:
            self.console.print("[yellow]Usage: /watch <url>[/yellow]")
            return
        
        video_id = self.yt_extractor.get_video_id(args)
        video = self.yt_extractor.get_video_info(video_id)
        
        if video:
            embed_url = self.yt_extractor.get_embed_url(video_id)
            self.console.print(f"[cyan]Opening:[/cyan] {video.title}")
            self.console.print(f"[blue]{embed_url}[/blue]")
            
            self.youtube.add_video(args)
        else:
            self.console.print("[red]Video not found[/red]")

    async def _cmd_run(self, args: str) -> None:
        """Run code in sandbox."""
        parts = args.split(None, 2)
        if len(parts) < 2:
            self.console.print("[yellow]Usage: /run <language> <code>[/yellow]")
            return

        language = parts[0].lower()
        code = parts[1]

        result = self.sandbox.execute(code, language)

        if result.success:
            self.console.print(Panel(
                f"[green]Output:[/green]\n{result.output[:500]}",
                title=f"Execution Complete ({result.execution_time:.2f}s)"
            ))
        else:
            self.console.print(f"[red]Error:[/red] {result.error}")

    async def _cmd_update(self, args: str) -> None:
        """Self-update commands."""
        parts = args.split(None, 1)
        cmd = parts[0].lower() if parts else "check"

        if cmd == "check":
            info = self.updater.check_for_updates()
            self.console.print(Panel(
                f"**Current:** {info['current_version']}\n"
                f"**Up to date:** {info['up_to_date']}\n"
                f"**Last checked:** {info['last_checked'][:10]}",
                title="Update Status",
                border_style="green"
            ))

        elif cmd == "verify":
            verified = self.updater.verify_integrity()
            if verified:
                self.console.print("[green]Integrity verified[/green]")
            else:
                self.console.print("[red]Integrity check failed![/red]")

        else:
            self.console.print("[cyan]/update check|verify[/cyan]")

    async def _cmd_patch(self, args: str) -> None:
        """Apply patches to source."""
        parts = args.split(None, 2)
        if len(parts) < 3:
            self.console.print("[yellow]Usage: /patch <file> <old> <new>[/yellow]")
            return

        file_path = parts[0]
        old = parts[1]
        new = parts[2]

        success, count = self.code_editor.replace_in_file(file_path, old, new)
        if success:
            self.console.print(f"[green]Replaced {count}x in {file_path}[/green]")
        else:
            self.console.print(f"[red]Failed to patch {file_path}[/red]")

    def _cmd_info(self, args: str) -> None:
        """Show source file info."""
        if not args:
            self.console.print("[yellow]Usage: /info <module>[/yellow]")
            return

        info = self.updater.get_source_info(args)
        if info:
            self.console.print(Panel(
                f"**Language:** {info['language']}\n"
                f"**Lines:** {info['lines']}\n"
                f"**Functions:** {len(info['functions'])}\n"
                f"**Classes:** {len(info['classes'])}\n"
                f"**Hash:** {info['hash'][:16]}...",
                title=info["module"],
                border_style="green"
            ))
        else:
            self.console.print(f"[red]Module not found: {args}[/red]")

    async def _cmd_exec(self, args: str) -> None:
        """Execute file in sandbox."""
        if not args:
            self.console.print("[yellow]Usage: /exec <file> [language][/yellow]")
            return

        parts = args.split(None, 1)
        file_path = parts[0]
        language = parts[1].lower() if len(parts) > 1 else None

        result = self.sandbox.execute_file(file_path, language)

        if result.success:
            self.console.print(Panel(
                f"[green]{result.output[:500]}[/green]",
                title=f"Ran in {result.execution_time:.2f}s"
            ))
        else:
            self.console.print(f"[red]Error:[/red] {result.error}")

    def _quit(self) -> None:
        """Exit PHANTOM."""
        self.memory.save(self._session_id)
        self.soul.save_personality()
        self.console.print(f"[green]{self.soul.get_farewell()}[/green]")
        self._running = False


def main():
    """Main entry point."""
    config = Config.get_instance()

    try:
        app = PhantomApp(config)
        app.run()
    except KeyboardInterrupt:
        print("\n[dim]Exiting...[/dim]")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()