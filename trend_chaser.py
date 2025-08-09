from __future__ import annotations

from typing import Dict, List, Optional, Tuple, Any
import re

import openai

# Ensure environment is loaded
import config  # noqa: F401  (side-effect: loads .env)

from trend_retrieval import (
    get_tiktok_trending,
    fetch_youtube_trending_topics,
)
from video_tools import get_stock_video, format_vertical
from youtube_upload import youtube_authenticate, upload_video


openai.api_key = config.OPENAI_API_KEY


def _clean_hashtag_tag(tag: str) -> str:
    cleaned = tag.strip()
    if not cleaned:
        return ""
    if not cleaned.startswith("#"):
        cleaned = f"#{cleaned}"
    return re.sub(r"\s+", "", cleaned)


def detect_trend(
    source: str = "tiktok",
    region: str = "US",
    max_youtube_results: int = 25,
) -> Tuple[str, Dict[str, Any]]:
    """Detect a trending topic from TikTok or YouTube.

    Returns (topic_text, metadata).
    """
    source_lower = (source or "").lower()

    if source_lower == "tiktok":
        trending = get_tiktok_trending()
        hashtags = trending.get("hashtags", [])
        sounds = trending.get("sounds", [])

        # Pick highest-count hashtag if available
        top_hashtag = None
        if hashtags:
            top_hashtag = max(hashtags, key=lambda h: int(h.get("count", 0) or 0))

        topic_text = (top_hashtag or {}).get("hashtag") or "viral"
        topic_text = topic_text.strip()

        metadata = {
            "source": "tiktok",
            "top_hashtag": top_hashtag,
            "top_sound": (max(sounds, key=lambda s: int(s.get("play_count", 0) or 0)) if sounds else None),
            "all_hashtags": hashtags,
            "all_sounds": sounds,
        }
        return topic_text, metadata

    # Default to YouTube
    yt_topics = fetch_youtube_trending_topics(region_code=region, max_results=max_youtube_results)
    topic_text = yt_topics[0] if yt_topics else "trending"
    return topic_text, {"source": "youtube", "topics": yt_topics}


def generate_script_for_trend(topic: str, hints: Optional[Dict[str, Any]] = None) -> str:
    """Use OpenAI to generate a short script tailored to the trend."""
    hints_text = ""
    if hints:
        if hints.get("source") == "tiktok":
            ht = hints.get("top_hashtag", {})
            hs = hints.get("top_sound", {})
            ht_text = _clean_hashtag_tag((ht or {}).get("hashtag", ""))
            sound_text = (hs or {}).get("sound_name")
            hints_text = f"Hashtag: {ht_text or 'n/a'}; Sound: {sound_text or 'n/a'}."

    prompt = (
        "Write a tight ~12-second YouTube Shorts script with a strong hook, 2-3 punchy lines, "
        "and a clear call to action. Align it to the current trend: '" + topic + "'. "
        "If relevant, adapt tone/style to match the trend."
    )
    if hints_text:
        prompt += f" Context hints: {hints_text}"

    resp = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message["content"].strip()


def build_title_and_tags(topic: str, metadata: Dict[str, Any]) -> Tuple[str, List[str]]:
    source = metadata.get("source")

    tags: List[str] = []
    if source == "tiktok":
        top_hashtag = (metadata.get("top_hashtag") or {}).get("hashtag")
        if top_hashtag:
            tags.append(top_hashtag)
        # Add a couple more popular hashtags if present
        for item in (metadata.get("all_hashtags") or [])[:3]:
            tag = item.get("hashtag")
            if tag and tag not in tags:
                tags.append(tag)

    title = f"{topic} #Shorts"
    return title, tags


def run_trend_chaser(
    source: str = "tiktok",
    region: str = "US",
    max_youtube_results: int = 25,
    upload: bool = True,
) -> Dict[str, Any]:
    """End-to-end: detect trend, generate script, produce vertical video, optionally upload.

    Returns a dict containing key artifacts (script text, video path, upload response if any).
    """
    topic, metadata = detect_trend(source=source, region=region, max_youtube_results=max_youtube_results)

    script_text = generate_script_for_trend(topic, hints=metadata)

    # Get stock clip and format vertical
    stock_path = get_stock_video(topic)
    vertical_path = format_vertical(stock_path)

    result: Dict[str, Any] = {
        "topic": topic,
        "metadata": metadata,
        "script": script_text,
        "vertical_path": vertical_path,
    }

    if upload:
        youtube = youtube_authenticate()
        title, tags = build_title_and_tags(topic, metadata)
        upload_resp = upload_video(
            youtube,
            vertical_path,
            title=title,
            description=script_text,
            tags=tags or [topic, "Shorts"],
        )
        result["upload_response"] = upload_resp

    return result


if __name__ == "__main__":
    out = run_trend_chaser(source="tiktok", upload=False)
    print("Trend Chaser result (upload disabled):")
    print({k: (v if k != "script" else v[:120] + "...") for k, v in out.items()})


