"""YouTube transcript ingestion worker.

Uses youtube-transcript-api for extracting video transcripts.
This is a gray area legally but widely used for AI applications.
"""

from __future__ import annotations

import re
from collections.abc import AsyncIterator
from typing import Any
from urllib.parse import parse_qs, urlparse

import httpx

from agent33.ingestion.base import BaseWorker, IngestResult

# Optional: use youtube-transcript-api if available
try:
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api._errors import (
        NoTranscriptFound,
        TranscriptsDisabled,
        VideoUnavailable,
    )
    HAS_TRANSCRIPT_API = True
except ImportError:
    HAS_TRANSCRIPT_API = False
    YouTubeTranscriptApi = None  # type: ignore
    NoTranscriptFound = Exception  # type: ignore
    TranscriptsDisabled = Exception  # type: ignore
    VideoUnavailable = Exception  # type: ignore


class YouTubeWorker(BaseWorker):
    """Worker that extracts transcripts from YouTube videos."""

    @property
    def source_type(self) -> str:
        return "youtube"

    async def fetch(self) -> AsyncIterator[IngestResult]:
        """Fetch transcripts from configured YouTube sources."""
        # Config can contain:
        # - video_ids: list of video IDs
        # - video_urls: list of video URLs
        # - channel_id: channel to fetch recent videos from (requires API key)
        # - playlist_id: playlist to fetch videos from

        video_ids = self.config.get("video_ids", [])
        video_urls = self.config.get("video_urls", [])

        # Extract IDs from URLs
        for url in video_urls:
            video_id = self._extract_video_id(url)
            if video_id and video_id not in video_ids:
                video_ids.append(video_id)

        if not video_ids:
            self._logger.warning("no_videos_configured")
            return

        self._logger.info("fetching_youtube_transcripts", video_count=len(video_ids))

        for video_id in video_ids:
            try:
                result = await self._fetch_video_transcript(video_id)
                if result:
                    yield result
            except Exception as e:
                self._logger.warning(
                    "video_fetch_failed",
                    video_id=video_id,
                    error=str(e),
                )
                continue

    async def _fetch_video_transcript(self, video_id: str) -> IngestResult | None:
        """Fetch transcript for a single video."""
        if not HAS_TRANSCRIPT_API:
            self._logger.error("youtube_transcript_api_not_installed")
            raise ImportError(
                "youtube-transcript-api is required for YouTube ingestion. "
                "Install with: pip install youtube-transcript-api"
            )

        # Get video metadata via oEmbed (no API key required)
        metadata = await self._fetch_video_metadata(video_id)

        try:
            # Try to get transcript (prefers manual captions, falls back to auto)
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

            # Try to get English transcript first
            transcript = None
            try:
                transcript = transcript_list.find_transcript(["en", "en-US", "en-GB"])
            except NoTranscriptFound:
                # Fall back to any available transcript, translated to English
                try:
                    transcript = transcript_list.find_generated_transcript(["en"])
                except NoTranscriptFound:
                    # Get first available and translate
                    for t in transcript_list:
                        try:
                            transcript = t.translate("en")
                            break
                        except Exception:
                            continue

            if transcript is None:
                self._logger.warning("no_transcript_available", video_id=video_id)
                return None

            # Fetch the actual transcript text
            transcript_data = transcript.fetch()

            # Combine transcript segments into full text
            full_text = self._combine_transcript(transcript_data)

            return IngestResult(
                source_url=f"https://www.youtube.com/watch?v={video_id}",
                title=metadata.get("title", f"YouTube Video {video_id}"),
                content=full_text,
                published_at=None,  # oEmbed doesn't provide this
                metadata={
                    "video_id": video_id,
                    "channel": metadata.get("author_name", ""),
                    "channel_url": metadata.get("author_url", ""),
                    "thumbnail_url": metadata.get("thumbnail_url", ""),
                    "duration_seconds": self._estimate_duration(transcript_data),
                    "transcript_type": transcript.is_generated and "auto" or "manual",
                    "language": transcript.language_code,
                },
            )

        except (NoTranscriptFound, TranscriptsDisabled) as e:
            self._logger.warning(
                "transcript_not_available",
                video_id=video_id,
                reason=str(e),
            )
            return None
        except VideoUnavailable:
            self._logger.warning("video_unavailable", video_id=video_id)
            return None

    async def _fetch_video_metadata(self, video_id: str) -> dict[str, Any]:
        """Fetch video metadata using YouTube oEmbed (no API key required)."""
        oembed_url = (
            f"https://www.youtube.com/oembed"
            f"?url=https://www.youtube.com/watch?v={video_id}"
            f"&format=json"
        )

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(oembed_url)
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            self._logger.debug("oembed_fetch_failed", video_id=video_id, error=str(e))

        return {}

    def _extract_video_id(self, url: str) -> str | None:
        """Extract video ID from various YouTube URL formats."""
        # Handle different URL formats:
        # - https://www.youtube.com/watch?v=VIDEO_ID
        # - https://youtu.be/VIDEO_ID
        # - https://www.youtube.com/embed/VIDEO_ID
        # - https://www.youtube.com/v/VIDEO_ID

        parsed = urlparse(url)

        if parsed.hostname in ("youtube.com", "www.youtube.com"):
            if parsed.path == "/watch":
                query = parse_qs(parsed.query)
                return query.get("v", [None])[0]
            elif parsed.path.startswith(("/embed/", "/v/")):
                return parsed.path.split("/")[2]
        elif parsed.hostname in ("youtu.be",):
            return parsed.path.lstrip("/")

        # Try regex as fallback
        match = re.search(r"(?:v=|/)([a-zA-Z0-9_-]{11})", url)
        return match.group(1) if match else None

    def _combine_transcript(self, transcript_data: list[dict]) -> str:
        """Combine transcript segments into readable text."""
        # Group segments into paragraphs (roughly every 30 seconds)
        paragraphs = []
        current_paragraph = []
        last_start = 0

        for segment in transcript_data:
            start = segment.get("start", 0)
            text = segment.get("text", "").strip()

            if not text:
                continue

            # Start new paragraph every ~30 seconds or on natural breaks
            if start - last_start > 30 and current_paragraph:
                paragraphs.append(" ".join(current_paragraph))
                current_paragraph = []

            current_paragraph.append(text)
            last_start = start

        if current_paragraph:
            paragraphs.append(" ".join(current_paragraph))

        return "\n\n".join(paragraphs)

    def _estimate_duration(self, transcript_data: list[dict]) -> int:
        """Estimate video duration from transcript timestamps."""
        if not transcript_data:
            return 0

        last_segment = transcript_data[-1]
        return int(last_segment.get("start", 0) + last_segment.get("duration", 0))
