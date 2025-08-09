import requests
import ffmpeg
import os
from config import PEXELS_API_KEY

def get_stock_video(query, out_path="stock.mp4"):
    url = f"https://api.pexels.com/videos/search?query={query}&per_page=1"
    headers = {"Authorization": PEXELS_API_KEY}
    r = requests.get(url, headers=headers).json()
    if not r.get("videos"):
        raise ValueError("No stock video found")
    video_url = r["videos"][0]["video_files"][0]["link"]
    vid_data = requests.get(video_url)
    with open(out_path, "wb") as f:
        f.write(vid_data.content)
    return out_path

def overlay_music(video_path, music_path, out_path="final_with_music.mp4"):
    (
        ffmpeg
        .input(video_path)
        .output(out_path)
        .run(overwrite_output=True)
    )
    return out_path

def format_vertical(video_path, out_path="vertical.mp4"):
    (
        ffmpeg
        .input(video_path)
        .filter("scale", 1080, 1920, force_original_aspect_ratio="decrease")
        .output(out_path, t=59)  # max 59 seconds
        .run(overwrite_output=True)
    )
    return out_path
