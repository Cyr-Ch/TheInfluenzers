from __future__ import annotations

from typing import Any, Dict, List, Optional

from googleapiclient.discovery import Resource

from youtube_upload import youtube_authenticate


def get_authenticated_youtube() -> Resource:
    """Authenticate via OAuth and return a YouTube Data API client."""
    return youtube_authenticate()


def get_my_channel(
    youtube: Resource, parts: List[str] | tuple[str, ...] = ("snippet", "statistics", "contentDetails")
) -> Optional[Dict[str, Any]]:
    """Return the channel resource for the authenticated user.

    parts can include: snippet, statistics, contentDetails, brandingSettings, topicDetails
    """
    request = youtube.channels().list(part=",".join(parts), mine=True)
    response = request.execute()
    items = response.get("items", [])
    return items[0] if items else None


def get_my_channel_statistics(youtube: Resource) -> Dict[str, Any]:
    """Return key statistics for the authenticated user's channel."""
    channel = get_my_channel(youtube, parts=("statistics",))
    stats = (channel or {}).get("statistics", {})
    return {
        "viewCount": int(stats.get("viewCount", 0) or 0),
        "subscriberCount": int(stats.get("subscriberCount", 0) or 0),
        "hiddenSubscriberCount": bool(stats.get("hiddenSubscriberCount", False)),
        "videoCount": int(stats.get("videoCount", 0) or 0),
    }


def get_my_channel_snippet(youtube: Resource) -> Dict[str, Any]:
    """Return the snippet (title, description, thumbnails) for the user's channel."""
    channel = get_my_channel(youtube, parts=("snippet",))
    return (channel or {}).get("snippet", {})


def get_my_uploads_playlist_id(youtube: Resource) -> Optional[str]:
    """Return the uploads playlist ID for the authenticated user's channel."""
    channel = get_my_channel(youtube, parts=("contentDetails",))
    if not channel:
        return None
    playlists = channel.get("contentDetails", {}).get("relatedPlaylists", {})
    return playlists.get("uploads")


def get_my_recent_uploads(
    youtube: Resource, max_results: int = 25
) -> List[Dict[str, Any]]:
    """Return recent uploaded videos (as playlistItems) from the channel's uploads playlist."""
    uploads_playlist_id = get_my_uploads_playlist_id(youtube)
    if not uploads_playlist_id:
        return []

    results: List[Dict[str, Any]] = []
    request = youtube.playlistItems().list(
        part="snippet,contentDetails",
        playlistId=uploads_playlist_id,
        maxResults=max(1, min(max_results, 50)),
    )

    while request is not None and len(results) < max_results:
        response = request.execute()
        items = response.get("items", [])
        results.extend(items)
        if len(results) >= max_results:
            break
        request = youtube.playlistItems().list_next(previous_request=request, previous_response=response)

    return results[:max_results]


def get_video_statistics(youtube: Resource, video_ids: List[str]) -> List[Dict[str, Any]]:
    """Return statistics for the given list of video IDs.

    The API allows up to 50 IDs per call; this function batches if needed.
    """
    output: List[Dict[str, Any]] = []
    for i in range(0, len(video_ids), 50):
        chunk = video_ids[i : i + 50]
        if not chunk:
            continue
        response = (
            youtube.videos()
            .list(part="id,statistics,snippet,contentDetails", id=",".join(chunk))
            .execute()
        )
        output.extend(response.get("items", []))
    return output


if __name__ == "__main__":
    yt = get_authenticated_youtube()
    stats = get_my_channel_statistics(yt)
    print("Channel statistics:", stats)
    recent = get_my_recent_uploads(yt, max_results=5)
    print(f"Recent uploads ({len(recent)}):", [it.get("contentDetails", {}).get("videoId") for it in recent])


