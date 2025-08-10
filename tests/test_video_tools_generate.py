from __future__ import annotations

import argparse
from pathlib import Path
import os
import sys
import time
from dotenv import load_dotenv

# Load .env before importing the module under test (video_tools reads env at import time)
load_dotenv()

# Import the module under test
sys.path.append(str(Path(__file__).resolve().parents[1]))
from video_tools import get_stock_video, generate_video_with_sora  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Integration test: generate one video via Azure OpenAI Sora")
    parser.add_argument("prompt", type=str, nargs="?", default="A captivating abstract neon tunnel animation",
                        help="Text prompt for the generated video")
    parser.add_argument("--out", type=str, default="sora_test.mp4",
                        help="Output file path (mp4)")
    parser.add_argument("--duration", type=int, default=6, help="Duration in seconds (1-20)")
    parser.add_argument("--aspect-ratio", type=str, default="9:16", help="Aspect ratio like 9:16, 16:9, 1:1")
    args = parser.parse_args()

    out_path = Path(args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print("Prompt:", args.prompt)
    print("Output:", str(out_path))

    t0 = time.time()
    try:
        # Prefer explicit Sora call to pass duration/aspect ratio
        video_path = generate_video_with_sora(
            args.prompt,
            out_path=str(out_path),
            duration_seconds=args.duration,
            aspect_ratio=args.aspect_ratio,
        )
    except Exception as e:
        print("Generation failed:", repr(e))
        print("Hint: Ensure AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY are set in your environment.")
        sys.exit(1)

    elapsed = time.time() - t0
    size_mb = out_path.stat().st_size / (1024 * 1024) if out_path.exists() else 0.0
    print(f"Done in {elapsed:.1f}s. Saved: {video_path} ({size_mb:.2f} MB)")


if __name__ == "__main__":
    main()


