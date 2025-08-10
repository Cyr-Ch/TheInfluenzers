import os
import time
import requests
from typing import Optional, Tuple

# ---- Azure OpenAI (Sora) config ----
AZURE_OPENAI_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.environ.get("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_API_VERSION = os.environ.get("OPENAI_API_VERSION", "preview")

if not AZURE_OPENAI_ENDPOINT:
    raise RuntimeError("AZURE_OPENAI_ENDPOINT must be set in environment")
if not AZURE_OPENAI_API_KEY:
    raise RuntimeError("AZURE_OPENAI_API_KEY must be set in environment")

HEADERS = {
    "api-key": AZURE_OPENAI_API_KEY,
    "Content-Type": "application/json"
}

def _aspect_ratio_to_dims(aspect_ratio: Optional[str], fallback: Tuple[int, int]) -> Tuple[int, int]:
    if not aspect_ratio:
        return fallback
    try:
        w_str, h_str = aspect_ratio.split(":")
        w, h = int(w_str), int(h_str)
        if (w, h) == (1, 1):
            return (720, 720)
        if (w, h) == (16, 9):
            return (1280, 720)
        if (w, h) == (9, 16):
            return (720, 1280)
        scale = 720 / h
        return (max(256, int(w * scale)), 720)
    except Exception:
        return fallback

def generate_video_with_sora(
    prompt: str,
    out_path: str = "sora_generated.mp4",
    duration_seconds: int = 10,
    aspect_ratio: Optional[str] = None,
    width: Optional[int] = None,
    height: Optional[int] = None,
    poll_interval_seconds: int = 5,
    request_timeout_seconds: int = 600,
    n_variants: int = 1,
    model: str = "sora",
) -> str:
    """Generate a video using Azure OpenAI Sora API and save it to out_path."""
    if width is None or height is None:
        width, height = _aspect_ratio_to_dims(aspect_ratio, fallback=(720, 720))

    n_seconds = max(1, min(int(duration_seconds), 20))

    # 1) Create generation job
    create_url = f"{AZURE_OPENAI_ENDPOINT}/openai/v1/video/generations/jobs?api-version={AZURE_OPENAI_API_VERSION}"
    payload = {
        "model": model,
        "prompt": prompt,
        "width": int(width),
        "height": int(height),
        "n_seconds": n_seconds,
        "n_variants": int(n_variants),
    }
    resp = requests.post(create_url, json=payload, headers=HEADERS, timeout=request_timeout_seconds)
    resp.raise_for_status()
    job_id = resp.json().get("id")
    if not job_id:
        raise RuntimeError(f"Unexpected Sora create response: {resp.json()}")

    # 2) Poll for completion
    status_url = f"{AZURE_OPENAI_ENDPOINT}/openai/v1/video/generations/jobs/{job_id}?api-version={AZURE_OPENAI_API_VERSION}"
    while True:
        time.sleep(poll_interval_seconds)
        status_resp = requests.get(status_url, headers=HEADERS, timeout=request_timeout_seconds)
        status_resp.raise_for_status()
        job_status = status_resp.json()
        status = job_status.get("status", "").lower()
        if status == "succeeded":
            break
        if status in ("failed", "cancelled"):
            raise RuntimeError(f"Video generation failed: {job_status}")

    generations = job_status.get("generations") or []
    if not generations:
        raise RuntimeError(f"No generations returned: {job_status}")

    # 3) Download first variant’s video
    generation_id = generations[0].get("id")
    content_url = f"{AZURE_OPENAI_ENDPOINT}/openai/v1/video/generations/{generation_id}/content/video?api-version={AZURE_OPENAI_API_VERSION}"
    video_resp = requests.get(content_url, headers=HEADERS, timeout=request_timeout_seconds)
    video_resp.raise_for_status()
    with open(out_path, "wb") as f:
        f.write(video_resp.content)
    return out_path

def get_stock_video(query, out_path="stock.mp4"):
    return generate_video_with_sora(
        prompt=query,
        out_path=out_path,
        duration_seconds=6,
    )
