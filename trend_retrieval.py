from __future__ import annotations

import logging
import os
import re
from typing import Dict, List, Any, Optional

import requests

# Ensure .env is loaded via the project config module
import config  # noqa: F401 (side-effect: loads .env)

"""
YouTube Captions Troubleshooting:

1. API Key Permissions: Your YouTube API key must have 'youtube.force-ssl' scope enabled
   in the Google Cloud Console to access the captions endpoint.

2. Caption Availability: Not all videos have captions. Auto-generated captions are more common
   than manual captions.

3. Language Matching: The system tries to find captions in the requested language, then falls
   back to auto-generated captions, then to any English captions.

4. Alternative Method: The youtube-transcript-api method is tried first as it's more reliable
   for auto-generated captions, then falls back to the YouTube Data API.

5. Debug Logging: Enable debug logging by uncommenting the logger.setLevel(logging.DEBUG) line
   to see detailed information about caption fetching.
"""

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# To enable debug logging for troubleshooting, uncomment the next line:
# logger.setLevel(logging.DEBUG)

# Environment variables
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
TIKTOK_RAPIDAPI_KEY = os.getenv("TIKTOK_RAPIDAPI_KEY")

# Constants
VALID_REGION_CODES = {
    "US", "GB", "CA", "AU", "DE", "FR", "JP", "IN", "BR", "MX", 
    "KR", "RU", "IT", "ES", "NL", "SE", "NO", "DK", "FI", "CH"
}

MUSIC_CATEGORY_ID = "10"
MAX_YOUTUBE_RESULTS = 50
YOUTUBE_VIDEO_ID_PATTERN = r'^[a-zA-Z0-9_-]{11}$'

# API endpoints
YOUTUBE_CAPTIONS_URL = "https://www.googleapis.com/youtube/v3/captions"
YOUTUBE_VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"
TIKTOK_HASHTAGS_URL = "https://api.apify.com/v2/acts/dtrungtin~tiktok-trending-hashtags/runs/last/dataset/items?clean=1"
TIKTOK_SOUNDS_URL = "https://api.apify.com/v2/acts/dtrungtin~tiktok-trending-sounds/runs/last/dataset/items?clean=1"


class ValidationError(ValueError):
    """Custom exception for validation errors."""
    pass


def validate_region_code(region_code: str) -> str:
    """Validate and normalize region code for YouTube API.
    
    Args:
        region_code: The region code to validate
        
    Returns:
        Normalized uppercase region code
        
    Raises:
        ValidationError: If region code is invalid
    """
    if not region_code:
        raise ValidationError("Region code cannot be empty")
    
    region_code = region_code.upper().strip()
    if region_code not in VALID_REGION_CODES:
        valid_codes = ", ".join(sorted(VALID_REGION_CODES))
        raise ValidationError(
            f"Invalid region code '{region_code}'. Valid codes are: {valid_codes}"
        )
    
    return region_code


def validate_video_id(video_id: str) -> str:
    """Validate YouTube video ID format.
    
    Args:
        video_id: The video ID to validate
        
    Returns:
        Validated video ID
        
    Raises:
        ValidationError: If video ID format is invalid
    """
    if not video_id:
        raise ValidationError("Video ID cannot be empty")
    
    if not re.match(YOUTUBE_VIDEO_ID_PATTERN, video_id):
        raise ValidationError(
            f"Invalid video ID format '{video_id}'. YouTube video IDs should be "
            "11 characters long and contain only letters, numbers, hyphens, and underscores."
        )
    
    return video_id


def validate_api_key(api_key: str, service_name: str = "YouTube") -> str:
    """Validate API key format.
    
    Args:
        api_key: The API key to validate
        service_name: Name of the service for error messages
        
    Returns:
        Validated API key
        
    Raises:
        ValidationError: If API key is invalid
    """
    if not api_key:
        raise ValidationError(f"{service_name} API key cannot be empty")
    
    if len(api_key) < 10:
        raise ValidationError(f"{service_name} API key appears to be too short")
    
    return api_key


def _convert_to_srt_format(transcript_data: List[Dict[str, Any]]) -> str:
    """Convert YouTube transcript data to SRT format.
    
    Args:
        transcript_data: Raw transcript data from YouTube
        
    Returns:
        SRT formatted string
    """
    srt_content = []
    
    for i, entry in enumerate(transcript_data, 1):
        start_time = int(entry['start'])
        duration = int(entry['duration'])
        end_time = start_time + duration
        
        # Convert to SRT timestamp format (HH:MM:SS,mmm)
        start_srt = f"{start_time//3600:02d}:{(start_time%3600)//60:02d}:{start_time%60:02d},{start_time%1*1000:03d}"
        end_srt = f"{end_time//3600:02d}:{(end_time%3600)//60:02d}:{end_time%60:02d},{end_time%1*1000:03d}"
        
        srt_content.append(f"{i}\n{start_srt} --> {end_srt}\n{entry['text']}")
    
    return "\n\n".join(srt_content)


def _get_captions_via_transcript_api(video_id: str, language: str) -> Optional[Dict[str, Any]]:
    """Get captions using youtube-transcript-api for auto-generated captions.
    
    Args:
        video_id: YouTube video ID
        language: Language code for captions
        
    Returns:
        Caption data dict or None if failed
    """
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        
        transcript_data = YouTubeTranscriptApi.fetch(video_id)
        srt_content = _convert_to_srt_format(transcript_data)
        
        return {
            "id": f"auto_{video_id}",
            "language": language,
            "is_auto": True,
            "content": srt_content,
            "format": "srt",
            "method": "youtube-transcript-api"
        }
        
    except ImportError:
        logger.warning("youtube-transcript-api not available, falling back to YouTube Data API")
        return None
    except Exception as e:
        logger.error(f"Alternative method failed for {video_id}: {e}")
        return None


def _get_captions_via_youtube_api(video_id: str, language: str, api_key: str) -> Optional[Dict[str, Any]]:
    """Get captions using YouTube Data API.
    
    Note: This endpoint requires the 'youtube.force-ssl' scope in your API key permissions.
    
    Args:
        video_id: YouTube video ID
        language: Language code for captions
        api_key: YouTube API key
        
    Returns:
        Caption data dict or None if failed
    """
    logger.info(f"Fetching captions via YouTube Data API for video {video_id} (language: {language})")
    
    params = {
        "part": "snippet",
        "videoId": video_id,
        "key": api_key
    }
    
    try:
        response = requests.get(YOUTUBE_CAPTIONS_URL, params=params, timeout=30)
        
        # Check for specific error codes
        if response.status_code == 403:
            logger.error(f"Permission denied for captions API. Check if your API key has 'youtube.force-ssl' scope.")
            return None
        elif response.status_code == 400:
            logger.error(f"Bad request for captions API: {response.text}")
            return None
        
        response.raise_for_status()
        data = response.json()
        
        caption_tracks = data.get("items", [])
        logger.info(f"Found {len(caption_tracks)} caption tracks for video {video_id}")
        
        if not caption_tracks:
            logger.info(f"No captions found for video {video_id}")
            # Log the response structure for debugging
            logger.debug(f"API response for {video_id}: {data}")
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error fetching captions for {video_id}: {e}")
        return None
    except ValueError as e:
        logger.error(f"Invalid JSON response for {video_id}: {e}")
        return None
    
    # Find the best caption track
    target_caption = _find_best_caption_track(caption_tracks, language)
    if not target_caption:
        logger.warning(f"No suitable caption track found for video {video_id}")
        # Log available caption tracks for debugging
        available_langs = [track.get("snippet", {}).get("language", "unknown") for track in caption_tracks]
        logger.debug(f"Available caption languages for {video_id}: {available_langs}")
        return None
    
    # Download caption content
    logger.info(f"Downloading caption content for track {target_caption.get('id')}")
    return _download_caption_content(target_caption, api_key)


def _find_best_caption_track(caption_tracks: List[Dict[str, Any]], language: str) -> Optional[Dict[str, Any]]:
    """Find the best caption track for the requested language.
    
    Args:
        caption_tracks: List of available caption tracks
        language: Requested language code
        
    Returns:
        Best matching caption track or None
    """
    if not caption_tracks:
        return None
    
    logger.debug(f"Found {len(caption_tracks)} caption tracks for language '{language}'")
    
    target_caption = None
    auto_caption = None
    any_language_caption = None
    
    for caption in caption_tracks:
        caption_lang = caption.get("snippet", {}).get("language", "")
        is_auto = caption.get("snippet", {}).get("trackKind", "") == "ASR"
        
        logger.debug(f"Caption track: lang='{caption_lang}', auto={is_auto}, id={caption.get('id')}")
        
        # Exact language match (preferred)
        if caption_lang == language and not is_auto:
            target_caption = caption
            logger.debug(f"Found exact language match: {caption_lang}")
            break
        elif caption_lang == language and is_auto:
            auto_caption = caption
            logger.debug(f"Found auto-generated caption for language: {caption_lang}")
        # Language starts with requested language (e.g., 'en' matches 'en-US')
        elif caption_lang.startswith(language) and not is_auto:
            target_caption = caption
            logger.debug(f"Found language prefix match: {caption_lang}")
            break
        # Any English caption as fallback
        elif caption_lang.startswith('en') and not is_auto:
            any_language_caption = caption
            logger.debug(f"Found English caption fallback: {caption_lang}")
    
    # Priority: exact match > prefix match > auto-generated > any English
    if target_caption:
        logger.info(f"Using caption track: {target_caption.get('snippet', {}).get('language')} (manual)")
        return target_caption
    elif auto_caption:
        logger.info(f"Using auto-generated caption: {auto_caption.get('snippet', {}).get('language')}")
        return auto_caption
    elif any_language_caption:
        logger.info(f"Using English caption fallback: {any_language_caption.get('snippet', {}).get('language')}")
        return any_language_caption
    
    logger.warning(f"No suitable caption track found for language '{language}'")
    return None


def _download_caption_content(caption_track: Dict[str, Any], api_key: str) -> Optional[Dict[str, Any]]:
    """Download caption content from YouTube.
    
    Args:
        caption_track: Caption track metadata
        api_key: YouTube API key
        
    Returns:
        Caption data dict or None if failed
    """
    caption_id = caption_track.get("id")
    download_params = {"key": api_key}
    
    # Try SRT format first, then VTT as fallback
    for fmt in ["srt", "vtt"]:
        download_params["tfmt"] = fmt
        
        try:
            response = requests.get(
                f"{YOUTUBE_CAPTIONS_URL}/{caption_id}",
                params=download_params,
                headers={"Accept": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                return {
                    "id": caption_id,
                    "language": caption_track.get("snippet", {}).get("language"),
                    "is_auto": caption_track.get("snippet", {}).get("trackKind") == "ASR",
                    "content": response.text,
                    "format": fmt,
                    "method": "youtube-data-api"
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error downloading captions: {e}")
        except Exception as e:
            logger.error(f"Error downloading captions: {e}")
    
    return None


def get_video_captions(
    video_id: str, 
    language: str = 'en', 
    api_key: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Get captions for a YouTube video with improved auto-generated caption support.
    
    Args:
        video_id: YouTube video ID
        language: Language code for captions (default: 'en')
        api_key: YouTube API key (optional, uses YOUTUBE_API_KEY from env if not provided)
    
    Returns:
        Dict with caption data or None if not available
    """
    # Validate inputs
    try:
        video_id = validate_video_id(video_id)
    except ValidationError as e:
        logger.error(f"Invalid video ID '{video_id}': {e}")
        return None
    
    # Try alternative method first for auto-generated captions (more reliable)
    captions = _get_captions_via_transcript_api(video_id, language)
    if captions:
        return captions
    
    # Fall back to YouTube Data API method
    key = api_key or YOUTUBE_API_KEY
    if not key:
        logger.error("YOUTUBE_API_KEY is not set. Add it to your .env or pass api_key explicitly.")
        return None
    
    # Validate API key
    try:
        key = validate_api_key(key, "YouTube")
    except ValidationError as e:
        logger.error(f"Invalid YouTube API key: {e}")
        return None
    
    return _get_captions_via_youtube_api(video_id, language, key)


def fetch_youtube_trending_videos(
    region_code: str = "US",
    max_results: int = 25,
    video_category_id: Optional[str] = None,
    include_captions: bool = False,
    caption_language: str = 'en',
    api_key: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Fetch trending YouTube videos using the YouTube Data API v3.

    Requires an API key in YOUTUBE_API_KEY or passed explicitly via api_key.
    
    Args:
        region_code: Country code for trending videos
        max_results: Maximum number of videos to fetch (max 50)
        video_category_id: Optional category filter
        include_captions: Whether to fetch captions for each video
        caption_language: Language code for captions (default: 'en')
        api_key: YouTube API key (optional)
    
    Returns:
        List of dicts with video info and optional captions
        
    Raises:
        RuntimeError: If API key is not available
        requests.RequestException: If API request fails
    """
    key = api_key or YOUTUBE_API_KEY
    if not key:
        raise RuntimeError(
            "YOUTUBE_API_KEY is not set. Add it to your .env or pass api_key explicitly."
        )

    # Validate and normalize inputs
    try:
        region_code = validate_region_code(region_code)
        key = validate_api_key(key, "YouTube")
    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        return []

    # Prepare API request
    params = {
        "part": "snippet,contentDetails,statistics",
        "chart": "mostPopular",
        "regionCode": region_code,
        "maxResults": max(1, min(max_results, MAX_YOUTUBE_RESULTS)),
        "key": key,
    }
    
    if video_category_id:
        params["videoCategoryId"] = video_category_id

    try:
        response = requests.get(YOUTUBE_VIDEOS_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        items = data.get("items", [])
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch trending videos: {e}")
        return []
    except ValueError as e:
        logger.error(f"Invalid response format: {e}")
        return []

    # Process video data
    results = []
    for item in items:
        video_data = _extract_video_data(item)
        
        # Add captions if requested
        if include_captions:
            logger.info(f"Fetching captions for video {video_data['id']}")
            captions = get_video_captions(
                video_data["id"], 
                language=caption_language, 
                api_key=key
            )
            video_data["captions"] = captions
        
        results.append(video_data)
    
    return results


def _extract_video_data(item: Dict[str, Any]) -> Dict[str, Any]:
    """Extract relevant data from YouTube API response item.
    
    Args:
        item: Raw video item from YouTube API
        
    Returns:
        Processed video data dictionary
    """
    snippet = item.get("snippet", {})
    statistics = item.get("statistics", {})
    
    return {
        "id": item.get("id"),
        "title": snippet.get("title"),
        "channelTitle": snippet.get("channelTitle"),
        "tags": snippet.get("tags", []),
        "categoryId": snippet.get("categoryId"),
        "description": snippet.get("description"),
        "publishedAt": snippet.get("publishedAt"),
        "viewCount": statistics.get("viewCount"),
        "likeCount": statistics.get("likeCount"),
        "commentCount": statistics.get("commentCount"),
    }


def fetch_youtube_trending_topics(
    region_code: str = "US",
    max_results: int = 25,
    api_key: Optional[str] = None,
) -> List[str]:
    """Return a list of trending topic titles from YouTube.
    
    Args:
        region_code: Country code for trending videos
        max_results: Maximum number of topics to fetch
        api_key: YouTube API key (optional)
        
    Returns:
        List of trending video titles
    """
    videos = fetch_youtube_trending_videos(
        region_code=region_code, 
        max_results=max_results, 
        api_key=api_key
    )
    return [v.get("title") for v in videos if v.get("title")]


def fetch_youtube_trending_music(
    region_code: str = "US",
    max_results: int = 25,
    api_key: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Return trending music videos (categoryId=10).
    
    Args:
        region_code: Country code for trending videos
        max_results: Maximum number of music videos to fetch
        api_key: YouTube API key (optional)
        
    Returns:
        List of trending music video data
    """
    try:
        return fetch_youtube_trending_videos(
            region_code=region_code,
            max_results=max_results,
            video_category_id=MUSIC_CATEGORY_ID,
            api_key=api_key,
        )
    except Exception as e:
        logger.error(f"Error fetching trending music: {e}")
        return []


def get_tiktok_trending(api_key: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
    """Fetch trending TikTok hashtags and sounds using Apify APIs.

    Optionally provide an Apify API token via `api_key` or set APIFY_API_TOKEN in the environment
    for higher rate limits.

    Args:
        api_key: Apify API token (optional)
        
    Returns:
        Dict with two lists:
            - hashtags: [{ 'hashtag': str, 'count': int }]
            - sounds: [{ 'sound_name': str, 'play_count': int }]
    """
    apify_token = api_key or os.getenv("APIFY_API_TOKEN")
    headers = {"Authorization": f"Bearer {apify_token}"} if apify_token else {}

    try:
        # Fetch both hashtags and sounds concurrently
        hashtags_response = requests.get(TIKTOK_HASHTAGS_URL, headers=headers, timeout=30)
        sounds_response = requests.get(TIKTOK_SOUNDS_URL, headers=headers, timeout=30)
        
        hashtags = _process_tiktok_hashtags(hashtags_response)
        sounds = _process_tiktok_sounds(sounds_response)
        
        return {"hashtags": hashtags, "sounds": sounds}
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch TikTok trending data: {e}")
        return {"hashtags": [], "sounds": []}


def _process_tiktok_hashtags(response: requests.Response) -> List[Dict[str, Any]]:
    """Process TikTok hashtags API response.
    
    Args:
        response: API response object
        
    Returns:
        List of processed hashtag data
    """
    hashtags = []
    
    if response.ok:
        try:
            for item in response.json():
                hashtags.append({
                    "hashtag": item.get("hashtag", ""),
                    "count": int(item.get("playCount", 0) or 0),
                })
        except Exception as e:
            logger.error(f"Error processing hashtags response: {e}")
    
    return hashtags


def _process_tiktok_sounds(response: requests.Response) -> List[Dict[str, Any]]:
    """Process TikTok sounds API response.
    
    Args:
        response: API response object
        
    Returns:
        List of processed sound data
    """
    sounds = []
    
    if response.ok:
        try:
            for item in response.json():
                sounds.append({
                    "sound_name": item.get("soundName", ""),
                    "play_count": int(item.get("playCount", 0) or 0),
                })
        except Exception as e:
            logger.error(f"Error processing sounds response: {e}")
    
    return sounds


def test_youtube_captions_api(api_key: Optional[str] = None) -> Dict[str, Any]:
    """Test the YouTube captions API to diagnose issues.
    
    Args:
        api_key: YouTube API key (optional)
        
    Returns:
        Dict with test results and API status
    """
    key = api_key or YOUTUBE_API_KEY
    if not key:
        return {"error": "No API key provided"}
    
    try:
        key = validate_api_key(key, "YouTube")
    except ValidationError as e:
        return {"error": f"Invalid API key: {e}"}
    
    # Test with a known video that should have captions
    test_video_id = "dQw4w9WgXcQ"  # Rick Roll - should have captions
    
    logger.info(f"Testing YouTube captions API with video: {test_video_id}")
    
    params = {
        "part": "snippet",
        "videoId": test_video_id,
        "key": key
    }
    
    try:
        response = requests.get(YOUTUBE_CAPTIONS_URL, params=params, timeout=30)
        logger.info(f"API response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            caption_tracks = data.get("items", [])
            logger.info(f"Found {len(caption_tracks)} caption tracks")
            
            # Log first few tracks for debugging
            for i, track in enumerate(caption_tracks[:3]):
                snippet = track.get("snippet", {})
                logger.info(f"Track {i+1}: lang={snippet.get('language')}, auto={snippet.get('trackKind') == 'ASR'}")
            
            return {
                "status": "success",
                "video_id": test_video_id,
                "caption_tracks_found": len(caption_tracks),
                "response_data": data
            }
        else:
            logger.error(f"API error: {response.status_code} - {response.text}")
            return {
                "status": "error",
                "status_code": response.status_code,
                "error_text": response.text
            }
            
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return {"status": "error", "exception": str(e)}