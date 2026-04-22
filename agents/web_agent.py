"""Web Agent - Web research, reading, crawling."""

import logging
from typing import Optional, Dict, Any, List

from agents.base_agent import BaseAgent
from tools.web_search import WebSearch
from tools.web_crawler import WebCrawler
from tools.web_viewer import WebViewer

logger = logging.getLogger("phantom.webagent")


class WebAgent(BaseAgent):
    """Agent for web research and crawling."""

    def __init__(self, *args, **kwargs):
        """Initialize web agent."""
        super().__init__(*args, **kwargs)
        self.searcher = WebSearch(self.config)
        self.crawler = WebCrawler(self.config)
        self.viewer = WebViewer(self.crawler)

    async def run(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Run web research task."""
        task_lower = task.lower()

        if task_lower.startswith("search "):
            query = task[7:]
            return await self.research(query)

        if task_lower.startswith("crawl "):
            url = task[6:]
            return await self.crawl_site(url)

        if task_lower.startswith("read "):
            url = task[5:]
            return await self.read_page(url)

        return await self.research(task)

    async def research(self, query: str, max_results: int = 10) -> str:
        """Research a topic."""
        results = self.searcher.search(query, max_results=max_results)

        if not results:
            return "No results found."

        output = f"## Research: {query}\n\n"

        for i, result in enumerate(results, 1):
            output += f"### {i}. {result.title}\n"
            output += f"[Source]({result.url})\n\n"
            output += f"{result.snippet}\n\n"

        return output

    async def crawl_site(
        self,
        url: str,
        max_pages: int = 20,
        max_depth: int = 3
    ) -> str:
        """Crawl a website."""
        sitemap = self.crawler.crawl_site(
            url,
            max_pages=max_pages,
            max_depth=max_depth
        )

        output = f"## Crawl Report: {url}\n\n"
        output += f"- Pages found: {len(sitemap.pages)}\n"
        output += f"- Total links: {sitemap.total_links}\n"
        output += f"- Time: {sitemap.crawl_time:.1f}s\n"
        output += f"- Errors: {len(sitemap.errors)}\n\n"

        self.viewer.render_sitemap(sitemap)

        return output

    async def read_page(self, url: str) -> str:
        """Read a single page."""
        text = self.crawler.read_url(url)

        if not text:
            return "Failed to fetch page."

        return text[:5000]

    async def analyze_headers(self, url: str) -> str:
        """Analyze security headers."""
        page = self.crawler.fetch_page(url)

        if not page:
            return "Failed to fetch page."

        self.viewer.render_security_headers(page.security_headers)

        return "Security headers analyzed."

    def get_capabilities(self) -> List[str]:
        """Get agent capabilities."""
        return [
            "web_search",
            "web_crawl",
            "page_read",
            "header_analysis",
        ]