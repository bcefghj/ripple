"""AI image generation via MiniMax image-01 API."""

from __future__ import annotations

import base64
import logging
from pathlib import Path

import httpx

from core.config import get_settings, IMAGES_DIR

log = logging.getLogger(__name__)

_TIMEOUT = httpx.Timeout(connect=10, read=120, write=10, pool=10)
_ENDPOINT = "https://api.minimax.io/v1/image_generation"


async def generate_image(
    prompt: str,
    *,
    filename: str = "cover.png",
    aspect_ratio: str = "3:4",
    n: int = 1,
    optimize_prompt: bool = True,
) -> list[Path]:
    """Generate image(s) and save to output/images/. Returns saved file paths."""
    s = get_settings()
    if not s.minimax_api_key:
        raise RuntimeError("MINIMAX_API_KEY not set — cannot generate images")

    headers = {
        "Authorization": f"Bearer {s.minimax_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": s.minimax_image_model,
        "prompt": prompt,
        "aspect_ratio": aspect_ratio,
        "response_format": "base64",
        "n": n,
        "prompt_optimizer": optimize_prompt,
    }

    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.post(_ENDPOINT, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()

    base_resp = data.get("base_resp", {})
    if base_resp.get("status_code", 0) != 0:
        raise RuntimeError(f"Image generation failed: {base_resp.get('status_msg')}")

    images_b64 = data.get("data", {}).get("image_base64", [])
    if not images_b64:
        raise RuntimeError("No images returned from API")

    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    stem = Path(filename).stem
    suffix = Path(filename).suffix or ".png"

    saved: list[Path] = []
    for i, b64 in enumerate(images_b64):
        name = f"{stem}_{i}{suffix}" if len(images_b64) > 1 else f"{stem}{suffix}"
        path = IMAGES_DIR / name
        path.write_bytes(base64.b64decode(b64))
        log.info("Saved image: %s", path)
        saved.append(path)

    return saved
