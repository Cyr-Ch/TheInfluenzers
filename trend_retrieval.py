from __future__ import annotations

from typing import Dict, List, Any, Optional
import os
import requests

# Ensure .env is loaded via the project config module
import config  # noqa: F401  (side-effect: loads .env)


YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
TIKTOK_RAPIDAPI_KEY = os.getenv("TIKTOK_RAPIDAPI_KEY")


def fetch_youtube_trending_videos(
    region_code: str = "US",
    max_results: int = 25,
    video_category_id: Optional[str] = None,
    api_key: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Fetch trending YouTube videos using the YouTube Data API v3.

    Requires an API key in YOUTUBE_API_KEY or passed explicitly via api_key.
    
    Returns a simplified list of dicts with id, title, channel, tags, and categoryId.
    """
    key = api_key or YOUTUBE_API_KEY
    if not key:
        raise RuntimeError(
            "YOUTUBE_API_KEY is not set. Add it to your .env or pass api_key explicitly."
        )

    params = {
        "part": "snippet,contentDetails,statistics",
        "chart": "mostPopular",
        "regionCode": region_code,
        "maxResults": max(1, min(max_results, 50)),  # API caps at 50 per page
        "key": key,
    }
    if video_category_id:
        params["videoCategoryId"] = video_category_id

    url = "https://www.googleapis.com/youtube/v3/videos"
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    data = resp.json()
    items = data.get("items", [])

    results: List[Dict[str, Any]] = []
    for item in items:
        snippet = item.get("snippet", {})
        results.append(
            {
                "id": item.get("id"),
                "title": snippet.get("title"),
                "channelTitle": snippet.get("channelTitle"),
                "tags": snippet.get("tags", []),
                "categoryId": snippet.get("categoryId"),
            }
        )
    return results


def fetch_youtube_trending_topics(
    region_code: str = "US",
    max_results: int = 25,
    api_key: Optional[str] = None,
) -> List[str]:
    """Return a list of trending topic titles from YouTube."""
    videos = fetch_youtube_trending_videos(
        region_code=region_code, max_results=max_results, api_key=api_key
    )
    return [v.get("title") for v in videos if v.get("title")]


def fetch_youtube_trending_music(
    region_code: str = "US",
    max_results: int = 25,
    api_key: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Return trending music videos (categoryId=10)."""
    MUSIC_CATEGORY_ID = "10"
    return fetch_youtube_trending_videos(
        region_code=region_code,
        max_results=max_results,
        video_category_id=MUSIC_CATEGORY_ID,
        api_key=api_key,
    )



def get_tiktok_trending(api_key: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
    """Fetch trending TikTok hashtags and sounds using Apify APIs.

    Optionally provide an Apify API token via `api_key` or set APIFY_API_TOKEN in the environment
    for higher rate limits.

    Returns a dict with two lists:
        - hashtags: [{ 'hashtag': str, 'count': int }]
        - sounds:   [{ 'sound_name': str, 'play_count': int }]
    """
    apify_token = api_key or os.getenv("APIFY_API_TOKEN")

    headers: Dict[str, str] = {}
    if apify_token:
        headers["Authorization"] = f"Bearer {apify_token}"

    hashtags_url = (
        "https://api.apify.com/v2/acts/dtrungtin~tiktok-trending-hashtags/runs/last/dataset/items?clean=1"
    )
    sounds_url = (
        "https://api.apify.com/v2/acts/dtrungtin~tiktok-trending-sounds/runs/last/dataset/items?clean=1"
    )

    hashtags_resp = requests.get(hashtags_url, headers=headers)
    sounds_resp = requests.get(sounds_url, headers=headers)

    hashtags: List[Dict[str, Any]] = []
    sounds: List[Dict[str, Any]] = []

    if hashtags_resp.ok:
        try:
            for item in hashtags_resp.json():
                hashtags.append(
                    {
                        "hashtag": item.get("hashtag", ""),
                        "count": int(item.get("playCount", 0) or 0),
                    }
                )
        except Exception:
            pass

    if sounds_resp.ok:
        try:
            for item in sounds_resp.json():
                sounds.append(
                    {
                        "sound_name": item.get("soundName", ""),
                        "play_count": int(item.get("playCount", 0) or 0),
                    }
                )
        except Exception:
            pass

    return {"hashtags": hashtags, "sounds": sounds}

