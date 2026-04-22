"""Self-Evolution Engine - PHANTOM continuously learns."""

import json
import logging
import time
import uuid
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime

from core.config import Config
from core.memory import ConversationMemory
from core.llm import LLMBackend
from tools.knowledge_base import KnowledgeBase
from core.thinking import ThinkingResult

logger = logging.getLogger("phantom.evolution")


@dataclass
class LearningResult:
    """Result of learning operation."""
    learned: str
    entries_added: int
    sources: List[str]


@dataclass
class EvolutionReport:
    """Evolution cycle report."""
    timestamp: str
    gaps_found: int
    searches_run: int
    entries_added: int
    kb_size_before: int
    kb_size_after: int
    cycle_number: int


class EvolutionEngine:
    """Self-learning evolution engine."""

    def __init__(
        self,
        config: Optional[Config] = None,
        memory: Optional[ConversationMemory] = None,
        llm: Optional[LLMBackend] = None,
        kb: Optional[KnowledgeBase] = None
    ):
        """Initialize evolution engine."""
        self.config = config or Config.get_instance()
        self.memory = memory or ConversationMemory(self.config)
        self.llm = llm or LLMBackend(self.config)
        self.kb = kb or KnowledgeBase(self.config)

        self._evolution_dir = self.config.config_dir / "evolution"
        self._evolution_dir.mkdir(parents=True, exist_ok=True)
        self._log_file = self._evolution_dir / "evolution_log.jsonl"
        self._gap_log_file = self._evolution_dir / "knowledge_gaps.jsonl"

        self.cycle_count = self._load_cycle_count()

    def _load_cycle_count(self) -> int:
        """Load current cycle count."""
        if self._log_file.exists():
            try:
                with open(self._log_file) as f:
                    lines = f.readlines()
                    if lines:
                        last = json.loads(lines[-1])
                        return last.get("cycle_number", 0)
            except Exception:
                pass
        return 0

    def extract_and_store(
        self,
        response: str,
        query: str
    ) -> None:
        """Extract and store knowledge from response."""
        if not self.config.evolution.passive_extraction:
            return

        try:
            extraction_prompt = f"""Extract structured knowledge from this response.
Return JSON only with this structure:
{{"facts": [], "tools": [], "cves": [], "techniques": []}}

Query: {query}
Response: {response[:2000]}"""

            messages = [
                {"role": "user", "content": extraction_prompt}
            ]

            result = self.llm.async_chat(messages)

            try:
                data = json.loads(result)
                facts = data.get("facts", [])
                tools = data.get("tools", [])
                cves = data.get("cves", [])
                techniques = data.get("techniques", [])

                for fact in facts[:5]:
                    if len(fact) > 20:
                        self.kb.add_entry(
                            category="techniques",
                            title=fact[:100],
                            content=fact,
                            tags=["extracted", "fact"]
                        )

                for tool in tools[:3]:
                    self.kb.add_entry(
                        category="tools",
                        title=tool,
                        content=tool,
                        tags=["extracted", "tool"]
                    )

                for cve in cves[:3]:
                    self.kb.add_entry(
                        category="cves",
                        title=cve,
                        content=cve,
                        tags=["extracted", "cve"]
                    )

            except json.JSONDecodeError:
                pass

        except Exception as e:
            logger.debug(f"Passive extraction failed: {e}")

    def learn_from_url(self, url: str) -> LearningResult:
        """Learn from URL content."""
        from tools.web_crawler import WebCrawler

        crawler = WebCrawler(self.config)
        page = crawler.fetch_page(url)

        if not page:
            return LearningResult(
                learned="Failed to fetch URL",
                entries_added=0,
                sources=[url]
            )

        try:
            summarization_prompt = f"""Extract key cybersecurity concepts, tools, techniques, and CVE references from this text.
Return JSON only:
{{"concepts": [], "tools": [], "techniques": [], "cves": []}}

Content: {page.text[:3000]}"""

            messages = [
                {"role": "user", "content": summarization_prompt}
            ]

            result = self.llm.async_chat(messages)
            entries_added = 0

            try:
                data = json.loads(result)

                for concept in data.get("concepts", []):
                    self.kb.add_entry(
                        category="techniques",
                        title=concept[:100],
                        content=concept,
                        tags=["learned", "url"],
                        source_url=url
                    )
                    entries_added += 1

                for tool in data.get("tools", []):
                    self.kb.add_entry(
                        category="tools",
                        title=tool,
                        content=tool,
                        tags=["learned", "url"],
                        source_url=url
                    )
                    entries_added += 1

            except json.JSONDecodeError:
                pass

            return LearningResult(
                learned=f"Learned {entries_added} entries from {url}",
                entries_added=entries_added,
                sources=[url]
            )

        except Exception as e:
            logger.error(f"Learn from URL failed: {e}")
            return LearningResult(
                learned=f"Error: {e}",
                entries_added=0,
                sources=[url]
            )

    def learn_from_search(self, topic: str) -> LearningResult:
        """Learn from web search."""
        from tools.web_search import WebSearch

        searcher = WebSearch(self.config)
        results = searcher.search(topic, max_results=3)

        entries_added = 0
        sources = []

        for result in results:
            sources.append(result.url)

            entry = self.kb.import_from_url(
                result.url,
                category="web_cache"
            )

            if entry:
                entries_added += 1

        return LearningResult(
            learned=f"Learned {entries_added} entries about {topic}",
            entries_added=entries_added,
            sources=sources
        )

    def learn_from_thinking(self, thinking_result: ThinkingResult) -> None:
        """Extract knowledge from thinking engine outputs."""
        if thinking_result.devil_output:
            self.kb.add_entry(
                category="techniques",
                title=f"Challenge: {thinking_result.query[:50]}",
                content=thinking_result.devil_output,
                tags=["devil-engine", "challenge"]
            )

        if thinking_result.meta_output:
            self.kb.add_entry(
                category="techniques",
                title=f"Meta-analysis: {thinking_result.query[:50]}",
                content=thinking_result.meta_output,
                tags=["meta-engine", "analysis"]
            )

        for suggestion in thinking_result.auto_search_suggestions:
            self.kb.add_entry(
                category="techniques",
                title=f"Search suggestion: {suggestion[:50]}",
                content=suggestion,
                tags=["suggested-search"]
            )

    def run_evolution_cycle(self) -> EvolutionReport:
        """Run full evolution cycle."""
        start_time = time.time()
        self.cycle_count += 1

        kb_size_before = len(self.kb._entries)

        recent_messages = self.memory.messages[-50:]
        topics = {}
        for msg in recent_messages:
            words = msg.content.lower().split()
            for word in words:
                if len(word) > 5:
                    topics[word] = topics.get(word, 0) + 1

        gaps = sorted(topics.items(), key=lambda x: x[1], reverse=True)[:5]

        searches_run = 0
        for topic, count in gaps:
            if count < 3:
                self.learn_from_search(topic)
                searches_run += 1

        from tools.web_search import WebSearch
        searcher = WebSearch(self.config)

        for topic, _ in gaps[:3]:
            try:
                cves = searcher.search_cve(topic)
                if cves:
                    self.kb.add_entry(
                        category="cves",
                        title=cves.cve_id,
                        content=f"{cves.description}",
                        tags=["cve-update", "evolution"],
                        source_url=f"https://nvd.nist.gov/vuln/detail/{cves.cve_id}"
                    )
            except Exception:
                pass

        kb_size_after = len(self.kb._entries)
        entries_added = kb_size_after - kb_size_before

        report = EvolutionReport(
            timestamp=datetime.now().isoformat(),
            gaps_found=len(gaps),
            searches_run=searches_run,
            entries_added=entries_added,
            kb_size_before=kb_size_before,
            kb_size_after=kb_size_after,
            cycle_number=self.cycle_count,
        )

        with open(self._log_file, "a") as f:
            f.write(json.dumps(report.__dict__) + "\n")

        elapsed = time.time() - start_time
        logger.info(
            f"Evolution cycle {self.cycle_count} complete in {elapsed:.2f}s"
        )

        return report

    def log_knowledge_gap(
        self,
        gap: str,
        importance: str = "MEDIUM"
    ) -> None:
        """Log a knowledge gap for later resolution."""
        with open(self._gap_log_file, "a") as f:
            f.write(json.dumps({
                "gap": gap,
                "importance": importance,
                "timestamp": datetime.now().isoformat(),
                "resolved": False,
            }) + "\n")

    def get_unresolved_gaps(self) -> List[Dict[str, Any]]:
        """Get unresolved knowledge gaps."""
        gaps = []

        if self._gap_log_file.exists():
            with open(self._gap_log_file) as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        if not data.get("resolved"):
                            gaps.append(data)
                    except json.JSONDecodeError:
                        pass

        return gaps