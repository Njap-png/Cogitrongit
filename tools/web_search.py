"""Web Search - Multi-engine search with smart auto-routing."""

import json
import logging
import time
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime
import requests
import re

from core.config import Config

logger = logging.getLogger("phantom.websearch")

CVE_PATTERN = re.compile(r'CVE-\d{4}-\d{4,}', re.IGNORECASE)
IP_PATTERN = re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b')
ATTACK_PATTERN = re.compile(r'T\d{4}', re.IGNORECASE)


@dataclass
class SearchResult:
    """Search result container."""
    title: str
    url: str
    snippet: str
    date: Optional[str] = None
    source: str = "web"


@dataclass
class CVEResult:
    """CVE search result."""
    cve_id: str
    description: str
    cvss_score: Optional[float] = None
    cvss_vector: Optional[str] = None
    severity: str = "UNKNOWN"
    affected: List[str] = None
    references: List[str] = None
    published: str = ""
    llm_explanation: str = ""


@dataclass
class ShodanResult:
    """Shodan search result."""
    ip_str: str
    port: int
    transport: str
    product: str = ""
    version: str = ""
    hostnames: List[str] = None
    tags: List[str] = None
    data: str = ""


@dataclass
class MITREResult:
    """MITRE ATT&CK result."""
    technique_id: str
    name: str
    description: str
    tactics: List[str] = None
    platforms: List[str] = None
    data_sources: List[str] = None


class WebSearch:
    """Multi-engine web search with smart routing."""

    def __init__(self, config: Optional[Config] = None):
        """Initialize web search."""
        self.config = config or Config.get_instance()
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": self.config.web.user_agent
        })

    def search(
        self,
        query: str,
        engine: str = "auto",
        max_results: int = 10
    ) -> List[SearchResult]:
        """Run web search with auto-routing."""
        if engine == "auto":
            engine = self._auto_route(query)

        try:
            if engine == "duckduckgo":
                return self._search_duckduckgo(query, max_results)
            elif engine == "searxng":
                return self._search_searxng(query, max_results)
            elif engine == "google":
                return self._search_google(query, max_results)
            else:
                return self._search_duckduckgo(query, max_results)
        except Exception as e:
            logger.error(f"Search error: {e}")
            return self._search_duckduckgo(query, max_results)

    def _auto_route(self, query: str) -> str:
        """Route to appropriate search engine."""
        query_lower = query.lower()

        if CVE_PATTERN.search(query):
            return "nvd"
        if "exploit" in query_lower or "poc" in query_lower:
            return "exploitdb"
        if "host:" in query_lower or IP_PATTERN.search(query):
            return "shodan"
        if ATTACK_PATTERN.search(query):
            return "mitre"
        if "code" in query_lower or "github" in query_lower:
            return "github"

        if self.config.web.searxng_url:
            return "searxng"
        return "duckduckgo"

    def _search_duckduckgo(self, query: str, max_results: int) -> List[SearchResult]:
        """Search using DuckDuckGo."""
        try:
            from duckduckgo_search import DDGS
            results = []
            with DDGS() as ddgs:
                for r in ddgs.news(query, max_results=max_results):
                    results.append(SearchResult(
                        title=r.get("title", ""),
                        url=r.get("url", ""),
                        snippet=r.get("body", "")[:200],
                        date=r.get("published", None),
                        source="duckduckgo"
                    ))
                    if len(results) >= max_results:
                        break
            return results
        except ImportError:
            try:
                url = "https://api.duckduckgo.com/"
                params = {
                    "q": query,
                    "format": "json",
                    "no_html": 1
                }
                response = self._session.get(url, params=params, timeout=self.config.web.timeout)
                data = response.json()
                results = []
                for topic in data.get("RelatedTopics", [])[:max_results]:
                    if "Text" in topic:
                        results.append(SearchResult(
                            title=query,
                            url=topic.get("URL", ""),
                            snippet=topic["Text"][:200],
                            source="duckduckgo"
                        ))
                return results
            except Exception as e:
                logger.error(f"DuckDuckGo search failed: {e}")
                return []

    def _search_searxng(self, query: str, max_results: int) -> List[SearchResult]:
        """Search using SearXNG."""
        try:
            url = f"{self.config.web.searxng_url}/search"
            params = {
                "q": query,
                "format": "json",
                "engines": "duckduckgo"
            }
            response = self._session.get(url, params=params, timeout=self.config.web.timeout)
            data = response.json()
            results = []
            for r in data.get("results", [])[:max_results]:
                results.append(SearchResult(
                    title=r.get("title", ""),
                    url=r.get("url", ""),
                    snippet=r.get("content", "")[:200],
                    source="searxng"
                ))
            return results
        except Exception as e:
            logger.error(f"SearXNG search failed: {e}")
            return []

    def _search_google(self, query: str, max_results: int) -> List[SearchResult]:
        """Search using Google CSE."""
        try:
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                "key": self.config.web.google_cse_key,
                "cx": self.config.web.google_cse_id,
                "q": query,
                "num": max_results
            }
            response = self._session.get(url, params=params, timeout=self.config.web.timeout)
            data = response.json()
            results = []
            for item in data.get("items", []):
                results.append(SearchResult(
                    title=item.get("title", ""),
                    url=item.get("link", ""),
                    snippet=item.get("snippet", "")[:200],
                    source="google"
                ))
            return results
        except Exception as e:
            logger.error(f"Google CSE search failed: {e}")
            return []

    def search_cve(self, cve_id: str) -> Optional[CVEResult]:
        """Fetch CVE details from NVD."""
        try:
            url = f"https://services.nvd.nist.gov/rest/json/cves/2.0"
            params = {"cveId": cve_id.upper()}
            response = self._session.get(url, params=params, timeout=self.config.web.timeout)
            data = response.json()

            if data.get("totalResults", 0) > 0:
                cve_data = data["vulnerabilities"][0]["cve"]
                description = cve_data.get("descriptions", [{}])[0].get("value", "")
                metrics = cve_data.get("metrics", {})
                cvss = metrics.get("cvssMetricV31", [{}])[0].get("cvssData", {})

                return CVEResult(
                    cve_id=cve_id.upper(),
                    description=description,
                    cvss_score=cvss.get("baseScore"),
                    cvss_vector=cvss.get("vectorString"),
                    severity=cvss.get("baseSeverity", "UNKNOWN"),
                    affected=[ref.get("url", "") for ref in cve_data.get("references", [])],
                    references=[ref.get("url", "") for ref in cve_data.get("references", [])],
                    published=cve_data.get("published", "")
                )
        except Exception as e:
            logger.error(f"CVE lookup failed: {e}")
        return None

    def search_exploit(self, query: str) -> List[SearchResult]:
        """Search ExploitDB."""
        try:
            url = "https://www.exploit-db.com/search"
            params = {"action": "search", "text": query}
            response = self._session.get(url, params=params, timeout=self.config.web.timeout)
            
            results = []
            results.append(SearchResult(
                title=f"ExploitDB Search: {query}",
                url=f"https://www.exploit-db.com/search?q={query}",
                snippet="Search ExploitDB for available exploits",
                source="exploitdb"
            ))
            return results
        except Exception as e:
            logger.error(f"ExploitDB search failed: {e}")
            return []

    def search_github(
        self,
        query: str,
        search_type: str = "code"
    ) -> List[SearchResult]:
        """Search GitHub."""
        try:
            headers = {}
            if self.config.web.github_token:
                headers["Authorization"] = f"token {self.config.web.github_token}"

            endpoint = "search/code" if search_type == "code" else "search/repositories"
            url = f"https://api.github.com/{endpoint}"
            params = {"q": query, "per_page": 10}

            response = self._session.get(
                url, params=params, headers=headers, timeout=self.config.web.timeout
            )
            data = response.json()
            results = []

            if search_type == "code":
                for item in data.get("items", []):
                    results.append(SearchResult(
                        title=item.get("name", ""),
                        url=item.get("html_url", ""),
                        snippet=item.get("path", ""),
                        source="github"
                    ))
            else:
                for item in data.get("items", []):
                    results.append(SearchResult(
                        title=item.get("full_name", ""),
                        url=item.get("html_url", ""),
                        snippet=item.get("description", "")[:200],
                        source="github"
                    ))
            return results
        except Exception as e:
            logger.error(f"GitHub search failed: {e}")
            return []

    def search_shodan(self, query: str) -> List[ShodanResult]:
        """Search Shodan."""
        if not self.config.web.shodan_api_key:
            return []

        try:
            url = "https://api.shodan.io/shodan/host/search"
            params = {
                "key": self.config.web.shodan_api_key,
                "query": query
            }
            response = self._session.get(url, params=params, timeout=self.config.web.timeout)
            data = response.json()
            results = []

            for match in data.get("matches", []):
                results.append(ShodanResult(
                    ip_str=match.get("ip_str", ""),
                    port=match.get("port", 0),
                    transport=match.get("transport", ""),
                    product=match.get("product", ""),
                    version=match.get("version", ""),
                    hostnames=match.get("hostnames", []),
                    tags=match.get("tags", []),
                    data=match.get("data", "")
                ))
            return results
        except Exception as e:
            logger.error(f"Shodan search failed: {e}")
            return []

    def search_mitre(self, query: str) -> Optional[MITREResult]:
        """Search MITRE ATT&CK."""
        try:
            if ATTACK_PATTERN.match(query.upper()):
                tid = query.upper()
            else:
                tid = None

            if tid:
                url = f"https://attack.mitre.org/api/techniques/{tid}"
                response = self._session.get(url, timeout=self.config.web.timeout)
                if response.status_code == 200:
                    data = response.json()
                    return MITREResult(
                        technique_id=tid,
                        name=data.get("name", ""),
                        description=data.get("description", ""),
                        tactics=data.get("tactics", []),
                        platforms=data.get("platforms", []),
                        data_sources=data.get("data_sources", [])
                    )

            url = "https://attack.mitre.org/api/techniques"
            response = self._session.get(url, timeout=self.config.web.timeout)
            data = response.json()

            query_lower = query.lower()
            for technique in data:
                if query_lower in technique.get("name", "").lower():
                    return MITREResult(
                        technique_id=technique.get("technique_id", ""),
                        name=technique.get("name", ""),
                        description=technique.get("description", ""),
                        tactics=technique.get("tactics", []),
                        platforms=technique.get("platforms", []),
                        data_sources=technique.get("data_sources", [])
                    )
        except Exception as e:
            logger.error(f"MITRE search failed: {e}")
        return None

    def display_results(self, results: List[SearchResult]) -> None:
        """Display results as Rich table."""
        from rich.console import Console
        from rich.table import Table

        console = Console()
        table = Table(title="Search Results")
        table.add_column("#", style="cyan", width=3)
        table.add_column("Title", style="green")
        table.add_column("URL", style="blue", no_wrap=True)
        table.add_column("Source", style="dim")

        for i, result in enumerate(results, 1):
            table.add_row(
                str(i),
                result.title[:60] + "..." if len(result.title) > 60 else result.title,
                result.url[:50] + "..." if len(result.url) > 50 else result.url,
                result.source
            )

        console.print(table)