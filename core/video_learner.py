"""PHANTOM Web Video Learning - Learn from videos and media."""

import re
import json
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import urlparse, parse_qs

from core.config import Config

logger = logging.getLogger("phantom.video")


@dataclass
class VideoInfo:
    """Video information."""
    url: str
    title: str
    platform: str
    duration: Optional[int]
    views: Optional[int]
    description: str
    transcript: Optional[str]
    chapters: List[Dict[str, Any]]
    watched: bool
    completion: float
    notes: List[str]
    learned_topics: List[str]


@dataclass
class MediaSearchResult:
    """Media search result."""
    title: str
    url: str
    platform: str
    duration: Optional[str]
    channel: Optional[str]
    thumbnail: Optional[str]


class VideoLearner:
    """Learn from videos and media content."""

    PLATFORMS = {
        "youtube": {
            "name": "YouTube",
            "embed_url": "https://www.youtube.com/embed/{id}",
            "transcript_patterns": ["transcript", " captions", "subtitle"],
        },
        "youtube_shorts": {
            "name": "YouTube Shorts",
            "embed_url": "https://www.youtube.com/embed/shorts/{id}",
        },
        "vimeo": {
            "name": "Vimeo",
            "embed_url": "https://player.vimeo.com/video/{id}",
        },
        "bitchute": {
            "name": "BitChute",
            "embed_url": "https://www.bitchute.com/embed/{id}",
        },
        "odysee": {
            "name": "Odysee",
            "embed_url": "https://odysee.com/$/embed/{id}",
        },
        "bilibili": {
            "name": "Bilibili",
            "embed_url": "https://player.bilibili.com/player.html?bvid={id}",
        },
        "twitter": {
            "name": "Twitter/X Video",
            "embed_url": "https://twitter.com/i/videos/{id}",
        },
    }

    TOPICS = {
        "cybersecurity": ["hacking", "penetration testing", "cybersecurity", "infosec", "network security"],
        "programming": ["python", "programming", "coding", "development", "software"],
        "ctf": ["ctf", "capture the flag", "hackathon"],
        "malware": ["malware", "virus", "ransomware", "reverse engineering"],
        "osint": ["osint", "reconnaissance", "footprinting"],
        "websec": ["web security", "xss", "sqli", "web hacking"],
        "crypto": ["cryptography", "encryption", "hash", "crypto"],
    }

    def __init__(self, config: Optional[Config] = None):
        """Initialize video learner."""
        self.config = config or Config.get_instance()

        self.video_dir = self.config.config_dir / "videos"
        self.video_dir.mkdir(parents=True, exist_ok=True)

        self._videos: Dict[str, VideoInfo] = {}
        self._load_videos()

    def _load_videos(self) -> None:
        """Load saved video data."""
        videos_file = self.video_dir / "library.json"

        if videos_file.exists():
            try:
                data = json.loads(videos_file.read_text())
                for video_data in data.values():
                    self._videos[video_data["url"]] = VideoInfo(
                        url=video_data["url"],
                        title=video_data["title"],
                        platform=video_data["platform"],
                        duration=video_data.get("duration"),
                        views=video_data.get("views"),
                        description=video_data.get("description", ""),
                        transcript=video_data.get("transcript"),
                        chapters=video_data.get("chapters", []),
                        watched=video_data.get("watched", False),
                        completion=video_data.get("completion", 0.0),
                        notes=video_data.get("notes", []),
                        learned_topics=video_data.get("learned_topics", []),
                    )
            except Exception as e:
                logger.error(f"Failed to load videos: {e}")

    def _save_videos(self) -> None:
        """Save video data."""
        videos_file = self.video_dir / "library.json"

        data = {}
        for url, video in self._videos.items():
            data[url] = {
                "url": video.url,
                "title": video.title,
                "platform": video.platform,
                "duration": video.duration,
                "views": video.views,
                "description": video.description,
                "transcript": video.transcript,
                "chapters": video.chapters,
                "watched": video.watched,
                "completion": video.completion,
                "notes": video.notes,
                "learned_topics": video.learned_topics,
            }

        videos_file.write_text(json.dumps(data, indent=2))

    def detect_platform(self, url: str) -> Tuple[str, str]:
        """Detect video platform from URL."""
        parsed = urlparse(url)
        host = parsed.netloc.lower()

        if "youtube" in host or "youtu.be" in host:
            if "/shorts/" in url:
                return "youtube_shorts", self._extract_youtube_id(url, "shorts")
            return "youtube", self._extract_youtube_id(url)
        elif "vimeo" in host:
            return "vimeo", parsed.path.strip("/")
        elif "bitchute" in host:
            return "bitchute", parsed.path.strip("/")
        elif "odysee" in host:
            return "odysee", self._extract_odysee_id(url)
        elif "bilibili" in host:
            return "bilibili", self._extract_bilibili_id(url)
        elif "twitter" in host or "x.com" in host:
            return "twitter", parsed.path.strip("/")

        return "unknown", url

    def _extract_youtube_id(self, url: str, variant: str = "") -> str:
        """Extract YouTube video ID."""
        if "youtu.be" in url:
            return url.split("/")[-1].split("?")[0]

        if variant == "shorts":
            match = re.search(r"/shorts/([a-zA-Z0-9_-]+)", url)
            if match:
                return match.group(1)

        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        if "v" in params:
            return params["v"][0]

        return parsed.path.strip("/")

    def _extract_odysee_id(self, url: str) -> str:
        """Extract Odysee video ID."""
        match = re.search(r"/embed/([a-zA-Z0-9_-]+)", url)
        if match:
            return match.group(1)
        return url.split("/")[-1].split("?")[0]

    def _extract_bilibili_id(self, url: str) -> str:
        """Extract Bilibili video ID."""
        match = re.search(r"bvid=([a-zA-Z0-9]+)", url)
        if match:
            return match.group(1)
        return url.split("/")[-1].split("?")[0]

    def add_video(self, url: str, title: str, **kwargs) -> VideoInfo:
        """Add video to library."""
        platform, video_id = self.detect_platform(url)

        video = VideoInfo(
            url=url,
            title=title,
            platform=platform,
            duration=kwargs.get("duration"),
            views=kwargs.get("views"),
            description=kwargs.get("description", ""),
            transcript=kwargs.get("transcript"),
            chapters=kwargs.get("chapters", []),
            watched=False,
            completion=0.0,
            notes=[],
            learned_topics=[],
        )

        self._videos[url] = video
        self._save_videos()

        logger.info(f"Added video: {title} from {platform}")
        return video

    def get_video(self, url: str) -> Optional[VideoInfo]:
        """Get video info."""
        return self._videos.get(url)

    def update_progress(
        self,
        url: str,
        completion: float,
        watched: bool = True
    ) -> bool:
        """Update watching progress."""
        if url in self._videos:
            self._videos[url].completion = completion
            self._videos[url].watched = watched
            self._save_videos()
            return True
        return False

    def add_note(self, url: str, note: str) -> bool:
        """Add note to video."""
        if url in self._videos:
            self._videos[url].notes.append(note)
            self._save_videos()
            return True
        return False

    def add_learned_topic(self, url: str, topic: str) -> bool:
        """Mark topic as learned from video."""
        if url in self._videos:
            self._videos[url].learned_topics.append(topic)
            self._save_videos()
            return True
        return False

    def search_videos(self, query: str, topic: Optional[str] = None) -> List[VideoInfo]:
        """Search video library."""
        query_lower = query.lower()
        results = []

        for video in self._videos.values():
            if topic and video.platform != topic:
                continue

            if query_lower in video.title.lower():
                results.append(video)
            elif query_lower in video.description.lower():
                results.append(video)
            elif query_lower in " ".join(video.learned_topics).lower():
                results.append(video)

        return results

    def get_library_stats(self) -> Dict[str, Any]:
        """Get video library statistics."""
        total = len(self._videos)
        watched = sum(1 for v in self._videos.values() if v.watched)
        total_notes = sum(len(v.notes) for v in self._videos.values())
        total_topics = set()
        for v in self._videos.values():
            total_topics.update(v.learned_topics)

        by_platform = {}
        for video in self._videos.values():
            by_platform[video.platform] = by_platform.get(video.platform, 0) + 1

        return {
            "total_videos": total,
            "watched": watched,
            "completion": f"{watched/total*100:.0f}%" if total > 0 else "0%",
            "total_notes": total_notes,
            "unique_topics": len(total_topics),
            "by_platform": by_platform,
        }

    def export_library(self, path: str) -> str:
        """Export video library to Markdown."""
        output_file = Path(path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w") as f:
            f.write("# PHANTOM Video Library\n\n")

            for video in sorted(self._videos.values(), key=lambda v: v.title):
                f.write(f"## {video.title}\n\n")
                f.write(f"**Platform:** {video.platform}\n")
                f.write(f"**URL:** {video.url}\n")
                f.write(f"**Progress:** {video.completion:.0%}\n")
                if video.duration:
                    f.write(f"**Duration:** {video.duration}s\n")

                if video.description:
                    f.write(f"\n**Description:**\n{video.description}\n")

                if video.learned_topics:
                    f.write(f"\n**Topics Learned:**\n")
                    for topic in video.learned_topics:
                        f.write(f"- {topic}\n")

                if video.notes:
                    f.write(f"\n**Notes:**\n")
                    for note in video.notes:
                        f.write(f"- {note}\n")

                f.write("\n---\n\n")

        return str(output_file)

    def suggest_videos(self, topic: str) -> List[str]:
        """Suggest videos for a topic."""
        suggestions = []

        topic_lower = topic.lower()
        for platform, topics in self.TOPICS.items():
            if topic_lower in topics:
                suggestions.append(f"Search {platform} for: {topic}")
                break

        return suggestions if suggestions else [f"Search for videos about: {topic}"]