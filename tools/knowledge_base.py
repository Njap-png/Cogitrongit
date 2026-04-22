"""Knowledge Base - Persistent local knowledge store."""

import json
import logging
import time
import uuid
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from collections import Counter

from core.config import Config

logger = logging.getLogger("phantom.kb")


@dataclass
class KBEntry:
    """Knowledge base entry."""
    id: str
    category: str
    title: str
    content: str
    tags: List[str] = field(default_factory=list)
    source_url: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""
    access_count: int = 0


class KnowledgeBase:
    """Persistent knowledge store with keyword search."""

    CATEGORIES = [
        "techniques",
        "tools",
        "cves",
        "ctf",
        "web_cache",
        "evolution",
    ]

    def __init__(self, config: Optional[Config] = None):
        """Initialize knowledge base."""
        self.config = config or Config.get_instance()
        self._base_dir = self.config.config_dir / "knowledge"
        self._base_dir.mkdir(parents=True, exist_ok=True)
        self._entries: Dict[str, KBEntry] = {}
        self._index: Dict[str, List[str]] = {}

        for category in self.CATEGORIES:
            (self._base_dir / category).mkdir(
                parents=True, exist_ok=True
            )

        self._load_all()

    def _load_all(self) -> None:
        """Load all entries from disk."""
        self._entries.clear()
        self._index.clear()

        for category in self.CATEGORIES:
            category_dir = self._base_dir / category
            if not category_dir.exists():
                continue

            for entry_file in category_dir.glob("*.json"):
                try:
                    with open(entry_file) as f:
                        data = json.load(f)

                    entry = KBEntry(
                        id=data["id"],
                        category=data["category"],
                        title=data["title"],
                        content=data["content"],
                        tags=data.get("tags", []),
                        source_url=data.get("source_url"),
                        created_at=data.get("created_at", ""),
                        updated_at=data.get("updated_at", ""),
                        access_count=data.get("access_count", 0),
                    )

                    self._entries[entry.id] = entry

                    for keyword in self._extract_keywords(entry):
                        if keyword not in self._index:
                            self._index[keyword] = []
                        self._index[keyword].append(entry.id)

                except Exception as e:
                    logger.debug(f"Failed to load {entry_file}: {e}")

        logger.info(f"Loaded {len(self._entries)} KB entries")

    def _extract_keywords(self, entry: KBEntry) -> List[str]:
        """Extract keywords from entry."""
        text = f"{entry.title} {entry.content} {' '.join(entry.tags)}"
        words = text.lower().split()
        keywords = []

        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at",
            "to", "for", "of", "with", "by", "from", "is", "are",
            "was", "were", "be", "been", "being", "have", "has",
            "had", "do", "does", "did", "will", "would", "could",
            "should", "may", "might", "can", "this", "that", "these"
        }

        for word in words:
            word = "".join(c for c in word if c.isalnum())
            if len(word) > 2 and word not in stop_words:
                keywords.append(word)

        return keywords

    def add_entry(
        self,
        category: str,
        title: str,
        content: str,
        tags: List[str],
        source_url: Optional[str] = None
    ) -> str:
        """Add new entry to knowledge base."""
        if category not in self.CATEGORIES:
            raise ValueError(f"Invalid category: {category}")

        entry_id = str(uuid.uuid4())[:8]
        now = datetime.now().isoformat()

        entry = KBEntry(
            id=entry_id,
            category=category,
            title=title,
            content=content,
            tags=tags,
            source_url=source_url,
            created_at=now,
            updated_at=now,
            access_count=0,
        )

        self._save_entry(entry)

        self._entries[entry_id] = entry

        for keyword in self._extract_keywords(entry):
            if keyword not in self._index:
                self._index[keyword] = []
            self._index[keyword].append(entry_id)

        logger.info(f"Added KB entry: {entry_id} ({category})")
        return entry_id

    def _save_entry(self, entry: KBEntry) -> None:
        """Save entry to disk."""
        category_dir = self._base_dir / entry.category
        entry_file = category_dir / f"{entry.id}.json"

        data = {
            "id": entry.id,
            "category": entry.category,
            "title": entry.title,
            "content": entry.content,
            "tags": entry.tags,
            "source_url": entry.source_url,
            "created_at": entry.created_at,
            "updated_at": entry.updated_at,
            "access_count": entry.access_count,
        }

        with open(entry_file, "w") as f:
            json.dump(data, f, indent=2)

    def search(
        self,
        query: str,
        category: Optional[str] = None,
        top_k: int = 5
    ) -> List[KBEntry]:
        """Search knowledge base."""
        query_keywords = self._extract_keywords(
            KBEntry("", "", query, "", [])
        )

        scores: Dict[str, float] = {}

        for keyword in query_keywords:
            if keyword in self._index:
                for entry_id in self._index[keyword]:
                    scores[entry_id] = scores.get(entry_id, 0) + 1

        if not scores:
            for entry in self._entries.values():
                if query.lower() in entry.title.lower() or query.lower() in entry.content.lower():
                    scores[entry.id] = scores.get(entry.id, 0) + 0.5

        results = []
        for entry_id, score in sorted(
            scores.items(), key=lambda x: x[1], reverse=True
        ):
            entry = self._entries.get(entry_id)
            if not entry:
                continue

            if category and entry.category != category:
                continue

            entry.access_count += 1
            results.append(entry)

            if len(results) >= top_k:
                break

        return results

    def get(self, entry_id: str) -> Optional[KBEntry]:
        """Get specific entry."""
        return self._entries.get(entry_id)

    def import_from_url(
        self,
        url: str,
        category: str
    ) -> Optional[KBEntry]:
        """Import from URL."""
        from tools.web_crawler import WebCrawler

        if category not in self.CATEGORIES:
            return None

        crawler = WebCrawler(self.config)
        page = crawler.fetch_page(url)

        if not page:
            return None

        title = page.title
        content = page.text[:5000]

        tags = self._generate_tags(title, content)

        entry_id = self.add_entry(
            category=category,
            title=title,
            content=content,
            tags=tags,
            source_url=url
        )

        return self.get(entry_id)

    def import_from_text(
        self,
        text: str,
        title: str,
        category: str,
        tags: List[str]
    ) -> Optional[KBEntry]:
        """Import from text."""
        if category not in self.CATEGORIES:
            return None

        entry_id = self.add_entry(
            category=category,
            title=title,
            content=text,
            tags=tags
        )

        return self.get(entry_id)

    def _generate_tags(self, title: str, content: str) -> List[str]:
        """Generate tags from content."""
        text = f"{title} {content}"
        words = text.split()
        counter = Counter(words)
        tags = []

        for word, count in counter.most_common(20):
            word = word.lower().strip(".,!?;:")
            if len(word) > 3 and count >= 2:
                tags.append(word[:30])

        return tags[:10]

    def export_markdown(self, path: str) -> None:
        """Export all entries as Markdown."""
        output_file = Path(path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w") as f:
            f.write("# PHANTOM Knowledge Base\n\n")

            for category in self.CATEGORIES:
                entries = [
                    e for e in self._entries.values()
                    if e.category == category
                ]

                if not entries:
                    continue

                f.write(f"## {category.title()} ({len(entries)})\n\n")

                for entry in entries:
                    f.write(f"### {entry.title}\n\n")
                    f.write(f"{entry.content}\n\n")
                    f.write(f"Tags: {', '.join(entry.tags)}\n\n")
                    f.write(f"ID: {entry.id}\n")
                    if entry.source_url:
                        f.write(f"Source: {entry.source_url}\n")
                    f.write("\n---\n\n")

        logger.info(f"Exported KB to {path}")

    def stats(self) -> Dict[str, Any]:
        """Get statistics."""
        total = len(self._entries)
        by_category: Dict[str, int] = {}
        total_size = 0

        for entry in self._entries.values():
            by_category[entry.category] = by_category.get(entry.category, 0) + 1
            total_size += len(entry.content)

        return {
            "total_entries": total,
            "by_category": by_category,
            "total_size_kb": total_size // 1024,
            "last_updated": max(
                (e.updated_at for e in self._entries.values()),
                default=""
            ),
        }