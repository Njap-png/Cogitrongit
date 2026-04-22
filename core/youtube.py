"""PHANTOM YouTube Integration - Full video capabilities."""

import re
import json
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from urllib.parse import urlparse, parse_qs
import html

from core.config import Config

logger = logging.getLogger("phantom.youtube")

try:
    import yt_dlp
    YT_DLP_AVAILABLE = True
except ImportError:
    YT_DLP_AVAILABLE = False

try:
    from selenium import webdriver
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False


@dataclass
class YouTubeVideo:
    """Complete YouTube video information."""
    video_id: str
    title: str
    description: str
    channel: str
    channel_id: str
    duration: int
    view_count: int
    like_count: int
    upload_date: str
    tags: List[str] = field(default_factory=list)
    category: str = ""
    thumbnail_url: str = ""
    embed_url: str = ""
    subtitles: Dict[str, str] = field(default_factory=dict)
    chapters: List[Dict[str, Any]] = field(default_factory=list)
    transcript: str = ""
    auto_generated_transcript: str = ""
    comments: List[Dict[str, Any]] = field(default_factory=list)
    related_videos: List[str] = field(default_factory=list)
    watched: bool = False
    completion: float = 0.0
    notes: List[str] = field(default_factory=list)
    learned_concepts: List[str] = field(default_factory=list)
    favorite: bool = False


@dataclass  
class VideoSearchResult:
    """YouTube search result."""
    video_id: str
    title: str
    channel: str
    duration: str
    views: str
    upload_date: str
    url: str
    thumbnail: str


class YouTubeExtractor:
    """Extract data from YouTube videos."""

    BASE_URL = "https://www.youtube.com"
    YTDLP_FORMAT = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"

    def __init__(self, config: Optional[Config] = None):
        """Initialize YouTube extractor."""
        self.config = config or Config.get_instance()
        self.cache_dir = self.config.config_dir / "youtube"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._session_cache: Dict[str, YouTubeVideo] = {}

    def get_video_id(self, url_or_id: str) -> str:
        """Extract video ID from URL or return if already ID."""
        if len(url_or_id) == 11 and re.match(r"^[a-zA-Z0-9_-]{11}$", url_or_id):
            return url_or_id

        parsed = urlparse(url_or_id)
        
        if parsed.netloc == "youtu.be":
            return parsed.path.strip("/")
        
        if "/shorts/" in url_or_id:
            match = re.search(r"/shorts/([a-zA-Z0-9_-]{11})", url_or_id)
            if match:
                return match.group(1)
        
        params = parse_qs(parsed.query)
        if "v" in params:
            return params["v"][0]
        
        path = parsed.path.strip("/")
        if len(path) == 11:
            return path
        
        return url_or_id

    def get_video_info(self, url_or_id: str) -> Optional[YouTubeVideo]:
        """Get complete video information."""
        video_id = self.get_video_id(url_or_id)
        
        if video_id in self._session_cache:
            return self._session_cache[video_id]
        
        if YT_DLP_AVAILABLE:
            return self._get_with_ytdlp(video_id)
        else:
            return self._get_with_api_fallback(video_id)

    def _get_with_ytdlp(self, video_id: str) -> Optional[YouTubeVideo]:
        """Get video info using yt-dlp."""
        url = f"{self.BASE_URL}/watch?v={video_id}"
        
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
            "skip_download": True,
            "getthumbnail": True,
            "getdescription": True,
            "getduration": True,
            "getfilepath": True,
            "no_color": True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if info and info.get("id"):
                    return self._parse_ytdlp_info(info)
        except Exception as e:
            logger.error(f"yt-dlp error for {video_id}: {e}")
        
        return None

    def _get_with_api_fallback(self, video_id: str) -> Optional[YouTubeVideo]:
        """Fallback extraction without yt-dlp."""
        import requests
        
        url = f"https://www.youtube.com/watch?v={video_id}"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            html_content = response.text
            
            data = self._extract_player_data(html_content)
            
            if data:
                video = YouTubeVideo(
                    video_id=video_id,
                    title=data.get("title", "Unknown"),
                    description=data.get("description", ""),
                    channel=data.get("author", "Unknown"),
                    channel_id=data.get("channelId", ""),
                    duration=int(data.get("lengthSeconds", 0)),
                    view_count=int(data.get("viewCount", 0)),
                    like_count=0,
                    upload_date=data.get("publishDate", ""),
                    thumbnail_url=f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg",
                    embed_url=f"https://www.youtube.com/embed/{video_id}",
                )
                self._session_cache[video_id] = video
                return video
        except Exception as e:
            logger.error(f"API fallback error for {video_id}: {e}")
        
        return None

    def _parse_ytdlp_info(self, info: Dict) -> YouTubeVideo:
        """Parse yt-dlp info dictionary."""
        video_id = info.get("id", "")
        
        chapters = []
        for chapter in info.get("chapters", []) or []:
            chapters.append({
                "title": chapter.get("title", ""),
                "start_time": chapter.get("start_time", 0),
            })
        
        subtitles = {}
        for lang, subs in (info.get("subtitles") or {}).items():
            subtitles[lang] = subs[0].get("data", "") if subs else ""
        
        video = YouTubeVideo(
            video_id=video_id,
            title=info.get("title", "Unknown"),
            description=info.get("description", ""),
            channel=info.get("uploader", info.get("channel", "Unknown")),
            channel_id=info.get("channel_id", ""),
            duration=info.get("duration", 0) or 0,
            view_count=info.get("view_count", 0) or 0,
            like_count=info.get("like_count", 0) or 0,
            upload_date=info.get("upload_date", ""),
            tags=info.get("tags", []) or [],
            category=info.get("categories", [""])[0] if info.get("categories") else "",
            thumbnail_url=info.get("thumbnail") or f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg",
            embed_url=f"https://www.youtube.com/embed/{video_id}",
            chapters=chapters,
            subtitles=subtitles,
            related_videos=info.get("related_videos", []) or [],
        )
        
        self._session_cache[video_id] = video
        return video

    def _extract_player_data(self, html: str) -> Optional[Dict]:
        """Extract player data from HTML."""
        patterns = [
            r'"playerArgs"\s*:\s*\'({.*?})\\n\'"',
            r'"playerResponse"\s*:\s*({.*?})\s*</script>',
            r'ytInitialPlayerResponse\s*=\s*({.+?})\s*;',
            r'var\s+ytInitialPlayerResponse\s*=\s*({.+?})\s*;',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError:
                    pass
        
        return None

    def extract_transcript(self, video_id: str) -> str:
        """Extract video transcript/subtitles."""
        video = self.get_video_info(video_id)
        if not video:
            return ""
        
        if video.transcript:
            return video.transcript
        
        if YT_DLP_AVAILABLE:
            try:
                url = f"{self.BASE_URL}/watch?v={video_id}"
                ydl_opts = {
                    "writesubtitles": True,
                    "writeautomaticsub": True,
                    "skip_download": True,
                    "subtitleslangs": ["en"],
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    
                    subs = info.get("subtitles") or {}
                    auto_subs = info.get("automatic_captions") or {}
                    
                    all_subs = {**subs, **auto_subs}
                    
                    if "en" in all_subs:
                        return all_subs["en"][0].get("data", "")
                    elif all_subs:
                        first_lang = list(all_subs.keys())[0]
                        return all_subs[first_lang][0].get("data", "")
            except Exception as e:
                logger.error(f"Transcript extraction failed: {e}")
        
        return ""

    def extract_chapters(self, video_id: str) -> List[Dict[str, Any]]:
        """Extract video chapters with timestamps."""
        video = self.get_video_info(video_id)
        if video and video.chapters:
            return video.chapters
        
        import requests
        
        url = f"https://www.youtube.com/watch?v={video_id}"
        headers = {"User-Agent": "Mozilla/5.0"}
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            html = response.text
            
            chapters = []
            
            chapter_pattern = r'"label"\s*:\s*"([^"]+)".*?"startTimeMs"\s*:\s*"(\d+)"'
            matches = re.findall(chapter_pattern, html, re.DOTALL)
            
            for title, start_ms in matches:
                chapters.append({
                    "title": html.unescape(title),
                    "start_time": int(start_ms) // 1000,
                })
            
            if chapters:
                return chapters
        except Exception as e:
            logger.error(f"Chapter extraction failed: {e}")
        
        return []

    def search_videos(
        self,
        query: str,
        max_results: int = 10,
        safe_search: bool = True
    ) -> List[VideoSearchResult]:
        """Search YouTube videos."""
        import requests
        
        params = {
            "search_query": query,
            "sp": "CAI%253D" if safe_search else "CAMSAhABAgCPIE",
            "gl": "US",
            "hl": "en",
        }
        
        results = []
        
        if not YT_DLP_AVAILABLE:
            search_url = f"{self.BASE_URL}/results"
            headers = {"User-Agent": "Mozilla/5.0"}
            
            try:
                response = requests.get(search_url, params=params, headers=headers, timeout=30)
                html = response.text
                
                video_pattern = r'"videoId"\s*:\s*"([a-zA-Z0-9_-]{11})"'
                title_pattern = r'"title"\s*:\s*"runs"\s*,\s*"runs"\s*:\s*\[\{"text"\s*:\s*"([^"]+)"'
                channel_pattern = r'"ownerText"\s*:\s*"runs"\s*,\s*"runs"\s*:\s*\[\{"text"\s*:\s*"([^"]+)"'
                
                video_ids = re.findall(video_pattern, html)[:max_results]
                
                for vid in video_ids:
                    url = f"{self.BASE_URL}/watch?v={vid}"
                    results.append(VideoSearchResult(
                        video_id=vid,
                        title=f"Video {vid}",
                        channel="Unknown",
                        duration="",
                        views="",
                        upload_date="",
                        url=url,
                        thumbnail=f"https://img.youtube.com/vi/{vid}/hqdefault.jpg",
                    ))
            except Exception as e:
                logger.error(f"YouTube search failed: {e}")
        else:
            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "extract_flat": True,
                "default_search": "ytsearch",
            }
            
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    search_query = f"ytsearch{max_results}:{query}"
                    info = ydl.extract_info(search_query, download=False)
                    
                    if info and "entries" in info:
                        for entry in info["entries"]:
                            results.append(VideoSearchResult(
                                video_id=entry.get("id", ""),
                                title=entry.get("title", "Unknown"),
                                channel=entry.get("channel", "Unknown"),
                                duration=self._format_duration(entry.get("duration", 0)),
                                views=str(entry.get("view_count", 0)),
                                upload_date=entry.get("upload_date", ""),
                                url=entry.get("webpage_url", ""),
                                thumbnail=entry.get("thumbnail", ""),
                            ))
            except Exception as e:
                logger.error(f"YouTube search failed: {e}")
        
        return results[:max_results]

    def download_audio(self, video_id: str, output_path: str) -> Optional[str]:
        """Download video audio."""
        if not YT_DLP_AVAILABLE:
            return None
        
        url = f"{self.BASE_URL}/watch?v={video_id}"
        output_template = str(Path(output_path) / "%(title)s.%(ext)s")
        
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": output_template,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return info.get("filepath") if info else None
        except Exception as e:
            logger.error(f"Audio download failed: {e}")
            return None

    def get_recommendations(self, video_id: str) -> List[str]:
        """Get video recommendations."""
        video = self.get_video_info(video_id)
        if video and video.related_videos:
            return video.related_videos[:10]
        return []

    @staticmethod
    def _format_duration(seconds: int) -> str:
        """Format seconds to HH:MM:SS."""
        if seconds < 60:
            return f"0:{seconds}"
        elif seconds < 3600:
            return f"{seconds // 60}:{seconds % 60:02d}"
        else:
            h = seconds // 3600
            m = (seconds % 3600) // 60
            s = seconds % 60
            return f"{h}:{m:02d}:{s:02d}"

    @staticmethod
    def get_embed_url(video_id: str) -> str:
        """Get YouTube embed URL."""
        return f"https://www.youtube.com/embed/{video_id}"

    @staticmethod
    def get_thumbnail_url(
        video_id: str,
        quality: str = "maxresdefault"
    ) -> str:
        """Get thumbnail URL."""
        qualities = ["maxresdefault", "hqdefault", "mqdefault", "sddefault"]
        if quality not in qualities:
            quality = "hqdefault"
        return f"https://img.youtube.com/vi/{video_id}/{quality}.jpg"


class VideoLearning:
    """Complete video learning system."""

    SUPPORTED_PLATFORMS = [
        "youtube", "youtube_shorts",
        "vimeo", "bitchute", "odysee", 
        "bilibili", "twitter", "rumble"
    ]

    def __init__(self, config: Optional[Config] = None):
        """Initialize video learning."""
        self.config = config or Config.get_instance()
        self.youtube = YouTubeExtractor(config)
        
        self.video_dir = self.config.config_dir / "videos"
        self.video_dir.mkdir(parents=True, exist_ok=True)
        
        self._library: Dict[str, YouTubeVideo] = {}
        self._load_library()

    def _load_library(self) -> None:
        """Load video library."""
        library_file = self.video_dir / "library.json"
        
        if library_file.exists():
            try:
                data = json.loads(library_file.read_text())
                for video_id, video_data in data.items():
                    self._library[video_id] = YouTubeVideo(
                        video_id=video_data["video_id"],
                        title=video_data["title"],
                        description=video_data.get("description", ""),
                        channel=video_data.get("channel", ""),
                        channel_id=video_data.get("channel_id", ""),
                        duration=video_data.get("duration", 0),
                        view_count=video_data.get("view_count", 0),
                        like_count=video_data.get("like_count", 0),
                        upload_date=video_data.get("upload_date", ""),
                        tags=video_data.get("tags", []),
                        watched=video_data.get("watched", False),
                        completion=video_data.get("completion", 0.0),
                        notes=video_data.get("notes", []),
                        learned_concepts=video_data.get("learned_concepts", []),
                        favorite=video_data.get("favorite", False),
                    )
            except Exception as e:
                logger.error(f"Failed to load library: {e}")

    def _save_library(self) -> None:
        """Save video library."""
        library_file = self.video_dir / "library.json"
        
        data = {}
        for video_id, video in self._library.items():
            data[video_id] = {
                "video_id": video.video_id,
                "title": video.title,
                "description": video.description,
                "channel": video.channel,
                "channel_id": video.channel_id,
                "duration": video.duration,
                "view_count": video.view_count,
                "like_count": video.like_count,
                "upload_date": video.upload_date,
                "tags": video.tags,
                "watched": video.watched,
                "completion": video.completion,
                "notes": video.notes,
                "learned_concepts": video.learned_concepts,
                "favorite": video.favorite,
            }
        
        library_file.write_text(json.dumps(data, indent=2))

    def add_video(self, url: str) -> Optional[YouTubeVideo]:
        """Add video to library."""
        if "youtube" in url.lower() or "youtu.be" in url.lower():
            video_id = self.youtube.get_video_id(url)
            video = self.youtube.get_video_info(video_id)
        else:
            return None
        
        if video:
            self._library[video.video_id] = video
            self._save_library()
        
        return video

    def get_video(self, video_id: str) -> Optional[YouTubeVideo]:
        """Get video from library."""
        return self._library.get(video_id)

    def search_youtube(self, query: str, max_results: int = 10) -> List[VideoSearchResult]:
        """Search YouTube."""
        return self.youtube.search_videos(query, max_results)

    def extract_and_learn(self, video_id: str) -> Dict[str, Any]:
        """Extract content and learn from video."""
        video = self.get_video(video_id)
        if not video:
            video = self.youtube.get_video_info(video_id)
            if video:
                self._library[video.video_id] = video
        
        if not video:
            return {"success": False, "error": "Video not found"}
        
        concepts = []
        
        if video.chapters:
            concepts.extend([c["title"] for c in video.chapters])
        
        if video.tags:
            concepts.extend(video.tags)
        
        transcript = self.youtube.extract_transcript(video_id)
        if transcript:
            video.transcript = transcript
            concepts.append("transcript_available")
        
        chapters = self.youtube.extract_chapters(video_id)
        if chapters:
            video.chapters = chapters
            concepts.extend([c["title"] for c in chapters])
        
        for concept in concepts[:10]:
            if concept not in video.learned_concepts:
                video.learned_concepts.append(concept)
        
        self._save_library()
        
        return {
            "success": True,
            "title": video.title,
            "channel": video.channel,
            "duration": video.duration,
            "concepts": concepts,
            "has_transcript": bool(transcript),
            "chapters": len(chapters),
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get library statistics."""
        total = len(self._library)
        watched = sum(1 for v in self._library.values() if v.watched)
        favorites = sum(1 for v in self._library.values() if v.favorite)
        total_time = sum(v.duration for v in self._library.values())
        
        channels = {}
        for v in self._library.values():
            channels[v.channel] = channels.get(v.channel, 0) + 1
        
        return {
            "total_videos": total,
            "watched": watched,
            "favorites": favorites,
            "completion_rate": f"{watched/total*100:.0f}%" if total > 0 else "0%",
            "total_time_hours": total_time / 3600,
            "channels": channels,
            "youtube_available": YT_DLP_AVAILABLE,
        }

    def export_to_markdown(self, path: str) -> str:
        """Export library to Markdown."""
        output_file = Path(path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, "w") as f:
            f.write("# PHANTOM Video Learning Library\n\n")
            
            for video in sorted(self._library.values(), key=lambda v: v.title):
                status = "★" if video.favorite else "○"
                watch_status = "✓" if video.watched else "○"
                
                f.write(f"## {status} {video.title}\n\n")
                f.write(f"**Channel:** [{video.channel}](https://youtube.com/channel/{video.channel_id})\n")
                f.write(f"**Duration:** {self.youtube._format_duration(video.duration)}\n")
                f.write(f"**Views:** {video.view_count:,}\n")
                f.write(f"**Watched:** {watch_status}\n\n")
                
                if video.description:
                    f.write(f"**Description:**\n{video.description[:500]}...\n\n")
                
                if video.chapters:
                    f.write("**Chapters:**\n")
                    for ch in video.chapters:
                        ts = self.youtube._format_duration(ch["start_time"])
                        f.write(f"- [{ts}] {ch['title']}\n")
                    f.write("\n")
                
                if video.learned_concepts:
                    f.write("**Topics Learned:**\n")
                    for concept in video.learned_concepts:
                        f.write(f"- {concept}\n")
                    f.write("\n")
                
                if video.notes:
                    f.write("**Notes:**\n")
                    for note in video.notes:
                        f.write(f"- {note}\n")
                    f.write("\n")
                
                f.write(f"[Watch](https://youtube.com/watch?v={video.video_id}) | ")
                f.write(f"[Embed]({video.embed_url})\n\n")
                f.write("---\n\n")
        
        return str(output_file)