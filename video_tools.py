import requests
import ffmpeg
import time
from typing import Optional
from config import RUNWAY_API_KEY

RUNWAY_API_BASE = "https://api.runwayml.com/v1"


def generate_video_with_runway(
    prompt: str,
    out_path: str = "runway_generated.mp4",
    duration_seconds: int = 6,
    aspect_ratio: str = "9:16",
    poll_interval_seconds: int = 5,
    request_timeout_seconds: int = 30,
) -> str:
    """Generate a video from a text prompt using Runway's API and save it to out_path.

    Requires RUNWAY_API_KEY in the environment.
    """
    if not RUNWAY_API_KEY:
        raise RuntimeError("RUNWAY_API_KEY is not set in environment/.env")

    headers = {
        "Authorization": f"Bearer {RUNWAY_API_KEY}",
        "Content-Type": "application/json",
    }

    # Create generation task. Endpoint and payload may vary by model/provider version.
    # Adjust `model` or payload fields to match your Runway plan.
    create_payload = {
        "model": "gen-3-alpha",
        "promptText": prompt,
        "duration": max(1, min(duration_seconds, 10)),
        "ratio": aspect_ratio,
    }

    create_resp = requests.post(
        f"{RUNWAY_API_BASE}/generations",
        headers=headers,
        json=create_payload,
        timeout=request_timeout_seconds,
    )
    create_resp.raise_for_status()
    create_data = create_resp.json()

    task_id = (
        create_data.get("id")
        or create_data.get("taskId")
        or create_data.get("task_id")
    )
    if not task_id:
        raise RuntimeError(f"Unexpected Runway create response: {create_data}")

    # Poll for completion
    while True:
        status_resp = requests.get(
            f"{RUNWAY_API_BASE}/tasks/{task_id}",
            headers={"Authorization": f"Bearer {RUNWAY_API_KEY}"},
            timeout=request_timeout_seconds,
        )
        status_resp.raise_for_status()
        status_data = status_resp.json()
        status = (
            status_data.get("status")
            or status_data.get("state")
            or status_data.get("task", {}).get("status")
        )

        if status in {"SUCCEEDED", "COMPLETED", "succeeded", "completed", "done"}:
            break
        if status in {"FAILED", "CANCELED", "ERROR", "failed", "canceled", "error"}:
            raise RuntimeError(f"Runway generation failed: {status_data}")
        time.sleep(poll_interval_seconds)

    # Extract output URL
    output_url: Optional[str] = None
    for key in ("output", "outputs", "result", "results"):
        val = status_data.get(key)
        if isinstance(val, list) and val:
            first = val[0]
            output_url = (
                first.get("url")
                or first.get("assetUrl")
                or first.get("asset_url")
            )
            if output_url:
                break
        if isinstance(val, dict):
            output_url = (
                val.get("url")
                or val.get("assetUrl")
                or val.get("asset_url")
            )
            if output_url:
                break

    if not output_url:
        # Try common top-level fields
        output_url = (
            status_data.get("output_url")
            or status_data.get("assetUrl")
            or status_data.get("asset_url")
        )

    if not output_url:
        raise RuntimeError(f"Could not locate output URL in task response: {status_data}")

    # Download the generated video
    with requests.get(output_url, stream=True, timeout=request_timeout_seconds) as r:
        r.raise_for_status()
    with open(out_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

    return out_path

def get_stock_video(query, out_path="stock.mp4"):
    """Generate a 9:16 video for the given prompt using Runway."""
    return generate_video_with_runway(
        prompt=query,
        out_path=out_path,
        duration_seconds=6,
        aspect_ratio="9:16",
    )

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
