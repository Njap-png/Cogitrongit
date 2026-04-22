"""Web Crawler - Full-featured web content fetcher."""

import asyncio
import hashlib
import logging
import time
from pathlib import Path
from typing import Optional, List, Dict, Any, Set
from dataclasses import dataclass
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse, urljoin
import json
import re

import requests
import bs4
from bs4 import BeautifulSoup

from core.config import Config

logger = logging.getLogger("phantom.webcrawler")

IP_PRIVATE_PATTERN = re.compile(
    r'^(?:10\.|172\.(?:1[6-9]|2\d|3[01])\.|192\.168\.)'
    r'(?:[0-9]{1,3}\.){2}[0-9]{1,3}$'
)


@dataclass
class PageContent:
    """Fetched page content container."""
    url: str
    title: str
    text: str
    html: str
    links: List[str]
    security_headers: Dict[str, Any]
    status_code: int
    response_headers: Dict[str, str]
    fetched_at: str
    from_cache: bool
    word_count: int


@dataclass
class SecurityHeaderResult:
    """Security header analysis result."""
    name: str
    value: str
    status: str
    recommendation: str


@dataclass
class SiteMap:
    """Site crawl map."""
    start_url: str
    pages: List[Dict[str, Any]]
    total_links: int
    errors: List[Dict[str, str]]
    crawl_time: float


class WebCrawler:
    """Full-featured web content crawler."""

    SECURITY_HEADERS = [
        "x-frame-options",
        "content-security-policy",
        "strict-transport-security",
        "x-content-type-options",
        "x-xss-protection",
        "referrer-policy",
        "permissions-policy",
        "access-control-allow-origin",
    ]

    def __init__(self, config: Optional[Config] = None):
        """Initialize web crawler."""
        self.config = config or Config.get_instance()
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": self.config.web.user_agent
        })
        self._cache_dir = self.config.config_dir / "cache"
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._robots_txt: Dict[str, Set[str]] = {}

    def fetch_page(
        self,
        url: str,
        render_js: bool = False,
        cache: bool = True
    ) -> Optional[PageContent]:
        """Fetch and parse a web page."""
        if not self._validate_url(url):
            logger.error(f"Invalid URL: {url}")
            return None

        if cache:
            cached = self._get_from_cache(url)
            if cached:
                return cached

        try:
            response = self._session.get(
                url,
                timeout=self.config.web.timeout,
                allow_redirects=True
            )
            response.raise_for_status()

            html = response.text
            soup = BeautifulSoup(html, "lxml")

            title = self._extract_title(soup)
            text = self.extract_clean_text(html)
            links = self._extract_links(soup, url)
            security_headers = self._extract_security_headers(response.headers)

            page_content = PageContent(
                url=str(response.url),
                title=title,
                text=text,
                html=html,
                links=links,
                security_headers=security_headers,
                status_code=response.status_code,
                response_headers=dict(response.headers),
                fetched_at=datetime.now().isoformat(),
                from_cache=False,
                word_count=len(text.split())
            )

            if cache:
                self._save_to_cache(url, page_content)

            return page_content

        except Exception as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None

    def _validate_url(self, url: str) -> bool:
        """Validate URL for safety."""
        try:
            parsed = urlparse(url)

            if parsed.scheme not in ("http", "https"):
                return False

            if parsed.netloc:
                hostname = parsed.netloc.split(":")[0]
                if IP_PRIVATE_PATTERN.match(hostname):
                    return False
                if hostname in ("localhost", "127.0.0.1"):
                    return False
                if hostname.endswith(".local"):
                    return False

            return True
        except Exception:
            return False

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title."""
        title_tag = soup.find("title")
        if title_tag:
            return title_tag.get_text().strip()

        og_title = soup.find("meta", property="og:title")
        if og_title:
            return og_title.get("content", "").strip()

        h1 = soup.find("h1")
        if h1:
            return h1.get_text().strip()[:100]

        return "Untitled"

    def extract_clean_text(self, html: str) -> str:
        """Extract clean text from HTML."""
        try:
            soup = BeautifulSoup(html, "lxml")

            for tag in soup.find_all(["nav", "footer", "header", "aside"]):
                tag.decompose()

            for tag in soup.find_all(
                "script", "style", "noscript", "iframe", "form"
            ):
                tag.decompose()

            try:
                from readability import Document
                doc = Document(html)
                text = doc.summary()
                soup = BeautifulSoup(text, "lxml")
            except Exception:
                pass

            for tag in soup.find_all(
                "nav", "footer", "header", "aside", "div", "span"
            ):
                if tag.get("class") and any(
                    c in str(tag.get("class")).lower()
                    for c in ["nav", "footer", "header", "sidebar", "ad", "sidebar", "menu", "comment"]
                ):
                    tag.decompose()

            text = soup.get_text(separator="\n")

            lines = [
                line.strip()
                for line in text.split("\n")
                if line.strip()
            ]

            text = "\n".join(lines)

            while "\n\n\n" in text:
                text = text.replace("\n\n\n", "\n\n")

            return text.strip()

        except Exception as e:
            logger.error(f"Text extraction failed: {e}")
            return html

    def _extract_links(
        self,
        soup: BeautifulSoup,
        base_url: str
    ) -> List[str]:
        """Extract all links from page."""
        links = []
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            try:
                absolute_url = urljoin(base_url, href)
                if absolute_url.startswith(("http://", "https://")):
                    links.append(absolute_url)
            except Exception:
                pass
        return list(set(links))

    def _extract_security_headers(
        self,
        headers: requests.structures.CaseInsensitiveDict
    ) -> Dict[str, Any]:
        """Analyze security headers."""
        results = {}

        for header_name in self.SECURITY_HEADERS:
            header_value = headers.get(header_name, "")
            status = "MISSING"
            recommendation = "Add this header for better security"

            if header_value:
                status = "PRESENT"
                recommendation = "Good"

                if header_name == "x-frame-options":
                    if header_value.lower() not in ("deny", "sameorigin"):
                        status = "MISCONFIGURED"
                        recommendation = "Should be 'DENY' or 'SAMEORIGIN'"
                elif header_name == "content-security-policy":
                    if "unsafe-inline" in header_value.lower():
                        status = "MISCONFIGURED"
                        recommendation = "Avoid 'unsafe-inline' if possible"

            results[header_name] = SecurityHeaderResult(
                name=header_name,
                value=header_value,
                status=status,
                recommendation=recommendation
            )

        return results

    def crawl_site(
        self,
        start_url: str,
        max_pages: int = 20,
        max_depth: int = 3,
        respect_robots: bool = True
    ) -> SiteMap:
        """Crawl a website."""
        start_time = time.time()
        visited: Set[str] = set()
        pages: List[Dict[str, Any]] = []
        errors: List[Dict[str, str]] = []
        all_links: Set[str] = set()

        if respect_robots:
            robots_url = urljoin(start_url, "/robots.txt")
            try:
                response = self._session.get(
                    robots_url, timeout=10
                )
                if response.status_code == 200:
                    self._robots_txt[start_url] = self._parse_robots_txt(
                        response.text
                    )
            except Exception:
                pass

        def get_allowed_urls(base_url: str) -> Set[str]:
            if base_url not in self._robots_txt:
                return set()
            return self._robots_txt[base_url]

        queue = [(start_url, 0)]
        allowed = get_allowed_urls(start_url)

        with ThreadPoolExecutor(max_workers=3) as executor:
            while queue and len(visited) < max_pages:
                url, depth = queue.pop(0)

                if url in visited:
                    continue

                if allowed and url not in allowed:
                    continue

                visited.add(url)

                page = self.fetch_page(url, cache=False)

                if page:
                    pages.append({
                        "url": url,
                        "title": page.title,
                        "status": page.status_code,
                        "depth": depth,
                        "links": len(page.links)
                    })
                    all_links.update(page.links)

                    if depth < max_depth:
                        for link in page.links:
                            if link not in visited:
                                parsed = urlparse(link)
                                if parsed.netloc == urlparse(start_url).netloc:
                                    queue.append((link, depth + 1))

                    time.sleep(self.config.web.rate_limit_delay)
                else:
                    errors.append({
                        "url": url,
                        "error": "Fetch failed"
                    })

        return SiteMap(
            start_url=start_url,
            pages=pages,
            total_links=len(all_links),
            errors=errors,
            crawl_time=time.time() - start_time
        )

    def _parse_robots_txt(self, content: str) -> Set[str]:
        """Parse robots.txt file."""
        allowed = set()
        disallow = set()
        current_user_agent = None

        for line in content.split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if line.lower().startswith("user-agent:"):
                current_user_agent = line.split(":", 1)[1].strip()
            elif line.lower().startswith("disallow:"):
                path = line.split(":", 1)[1].strip()
                if current_user_agent == "*" or current_user_agent == "PHANTOM":
                    disallow.add(path)
            elif line.lower().startswith("allow:"):
                path = line.split(":", 1)[1].strip()
                if current_user_agent == "*" or current_user_agent == "PHANTOM":
                    allowed.add(path)

        return disallow - allowed

    def read_url(self, url: str) -> Optional[str]:
        """Convenience method to read URL content."""
        page = self.fetch_page(url)
        if page:
            return page.text
        return None

    async def fetch_multiple(self, urls: List[str]) -> List[PageContent]:
        """Fetch multiple URLs concurrently."""
        results = []
        semaphore = asyncio.Semaphore(
            self.config.web.max_concurrent_requests
        )

        async def fetch_one(url: str) -> Optional[PageContent]:
            async with semaphore:
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(
                    None, self.fetch_page, url
                )

        tasks = [fetch_one(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        return [
            r if isinstance(r, PageContent) else None
            for r in results
        ]

    def _get_from_cache(self, url: str) -> Optional[PageContent]:
        """Get page from cache."""
        if not self.config.web.cache_enabled:
            return None

        cache_key = hashlib.sha256(url.encode()).hexdigest()
        cache_file = self._cache_dir / f"{cache_key}.json"

        if cache_file.exists():
            try:
                age = time.time() - cache_file.stat().st_mtime
                ttl = self.config.web.cache_ttl_hours * 3600
                if age < ttl:
                    with open(cache_file) as f:
                        data = json.load(f)
                    return PageContent(
                        url=data["url"],
                        title=data["title"],
                        text=data["text"],
                        html=data["html"],
                        links=data["links"],
                        security_headers=data["security_headers"],
                        status_code=data["status_code"],
                        response_headers=data["response_headers"],
                        fetched_at=data["fetched_at"],
                        from_cache=True,
                        word_count=data["word_count"]
                    )
            except Exception as e:
                logger.debug(f"Cache read failed: {e}")

        return None

    def _save_to_cache(self, url: str, content: PageContent) -> None:
        """Save page to cache."""
        if not self.config.web.cache_enabled:
            return

        cache_key = hashlib.sha256(url.encode()).hexdigest()
        cache_file = self._cache_dir / f"{cache_key}.json"

        try:
            data = {
                "url": content.url,
                "title": content.title,
                "text": content.text,
                "html": content.html,
                "links": content.links,
                "security_headers": {
                    k: {
                        "name": v.name,
                        "value": v.value,
                        "status": v.status,
                        "recommendation": v.recommendation
                    }
                    for k, v in content.security_headers.items()
                },
                "status_code": content.status_code,
                "response_headers": dict(content.response_headers),
                "fetched_at": content.fetched_at,
                "word_count": content.word_count
            }
            with open(cache_file, "w") as f:
                json.dump(data, f)
        except Exception as e:
            logger.debug(f"Cache write failed: {e}")