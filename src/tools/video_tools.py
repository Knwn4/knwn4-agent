"""Video generation tools - API-based video/image models with smart selector."""
import logging
import time

import httpx

from src.config import (
    GEMINI_API_KEY,
    PI_API_KEY,
    OPENAI_API_KEY,
    FAL_KEY,
    MEDIA_OUTPUT_DIR,
)
from src.tools.registry import tool

logger = logging.getLogger(__name__)

# --- Model Selection Matrix ---
MODEL_MATRIX = {
    "cinematic": {"best": "veo3", "fallback": "kling_pro", "note": "Nature, city, establishing shots"},
    "talking_head": {"best": "heygen", "fallback": "higgsfield", "note": "Browser-based avatar"},
    "product_demo": {"best": "remotion", "fallback": "screen_capture", "note": "Local CLI"},
    "abstract": {"best": "flux_kling", "fallback": "minimax", "note": "Stylized visuals"},
    "avatar_expressive": {"best": "higgsfield", "fallback": "heygen", "note": "Browser-based"},
    "full_ai_video": {"best": "invideo", "fallback": "sora", "note": "Full prompt-to-video"},
    "motion_graphics": {"best": "remotion", "fallback": "ffmpeg", "note": "Data viz, titles"},
    "quick_talking_head": {"best": "heygen_api", "fallback": "elevenlabs_still", "note": "Scale"},
    "smooth_portrait": {"best": "minimax", "fallback": "kling_standard", "note": "Hailuo-style"},
    "surreal": {"best": "sora", "fallback": "veo3", "note": "Creative, dreamlike"},
}


@tool
def select_best_model(scene_type: str) -> dict:
    """Select the best video model for a given scene type.
    scene_type: Type of scene (cinematic, talking_head, product_demo, abstract, avatar_expressive, full_ai_video, motion_graphics, quick_talking_head, smooth_portrait, surreal)
    """
    if scene_type not in MODEL_MATRIX:
        return {
            "error": f"Unknown scene type: {scene_type}",
            "available_types": list(MODEL_MATRIX.keys()),
        }

    entry = MODEL_MATRIX[scene_type]
    return {
        "scene_type": scene_type,
        "recommended_model": entry["best"],
        "fallback_model": entry["fallback"],
        "note": entry["note"],
    }


@tool
async def generate_video_veo3(prompt: str, duration: int = 5) -> dict:
    """Generate cinematic video using Google Veo 3 via Vertex AI / Gemini.
    prompt: Detailed video description
    duration: Video duration in seconds (5-15)
    """
    async with httpx.AsyncClient() as client:
        # Gemini generative video endpoint
        response = await client.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/veo-3:generateVideos",
            params={"key": GEMINI_API_KEY},
            json={
                "prompt": prompt,
                "videoConfig": {"durationSeconds": duration},
            },
            timeout=120.0,
        )
        response.raise_for_status()
        data = response.json()

        # Veo 3 returns an operation ID for async polling
        operation_name = data.get("name", "")
        return {
            "status": "generating",
            "operation_id": operation_name,
            "model": "veo3",
            "prompt": prompt,
            "note": "Poll operation for completion. Video will be available at result URL.",
        }


@tool
async def generate_video_kling(
    prompt: str, mode: str = "pro", duration: int = 5, aspect_ratio: str = "9:16"
) -> dict:
    """Generate video using Kling via PiAPI.
    prompt: Video generation prompt
    mode: Quality mode (standard, pro)
    duration: Duration in seconds (5 or 10)
    aspect_ratio: Aspect ratio (16:9, 9:16, 1:1)
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.piapi.ai/api/v1/task",
            headers={"X-API-Key": PI_API_KEY},
            json={
                "model": "kling",
                "task_type": "video_generation",
                "input": {
                    "prompt": prompt,
                    "mode": mode,
                    "duration": str(duration),
                    "aspect_ratio": aspect_ratio,
                },
            },
            timeout=60.0,
        )
        response.raise_for_status()
        data = response.json()

        return {
            "status": "queued",
            "task_id": data.get("data", {}).get("task_id", ""),
            "model": f"kling_{mode}",
            "prompt": prompt,
        }


@tool
async def generate_video_minimax(prompt: str, aspect_ratio: str = "9:16") -> dict:
    """Generate smooth portrait video using Minimax/Hailuo via PiAPI.
    prompt: Video generation prompt
    aspect_ratio: Aspect ratio (16:9, 9:16, 1:1)
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.piapi.ai/api/v1/task",
            headers={"X-API-Key": PI_API_KEY},
            json={
                "model": "minimax",
                "task_type": "video_generation",
                "input": {
                    "prompt": prompt,
                    "aspect_ratio": aspect_ratio,
                },
            },
            timeout=60.0,
        )
        response.raise_for_status()
        data = response.json()

        return {
            "status": "queued",
            "task_id": data.get("data", {}).get("task_id", ""),
            "model": "minimax",
            "prompt": prompt,
        }


@tool
async def generate_video_sora(prompt: str, duration: int = 5, aspect_ratio: str = "9:16") -> dict:
    """Generate creative/surreal video using OpenAI Sora.
    prompt: Video generation prompt
    duration: Duration in seconds
    aspect_ratio: Aspect ratio (16:9, 9:16, 1:1)
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.openai.com/v1/video/generations",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
            json={
                "model": "sora",
                "prompt": prompt,
                "duration": duration,
                "aspect_ratio": aspect_ratio,
            },
            timeout=60.0,
        )
        response.raise_for_status()
        data = response.json()

        return {
            "status": "generating",
            "id": data.get("id", ""),
            "model": "sora",
            "prompt": prompt,
        }


@tool
async def generate_image_flux(prompt: str, aspect_ratio: str = "9:16") -> dict:
    """Generate image using fal.ai Flux for thumbnails or video input frames.
    prompt: Image generation prompt
    aspect_ratio: Aspect ratio (16:9, 9:16, 1:1, 4:3)
    """
    # Map aspect ratio to dimensions
    dimensions = {
        "16:9": {"width": 1920, "height": 1080},
        "9:16": {"width": 1080, "height": 1920},
        "1:1": {"width": 1080, "height": 1080},
        "4:3": {"width": 1440, "height": 1080},
    }
    dims = dimensions.get(aspect_ratio, dimensions["9:16"])

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://queue.fal.run/fal-ai/flux/dev",
            headers={"Authorization": f"Key {FAL_KEY}"},
            json={
                "prompt": prompt,
                "image_size": dims,
                "num_images": 1,
            },
            timeout=60.0,
        )
        response.raise_for_status()
        data = response.json()

        # fal.ai returns request_id for queue, or images directly
        if "request_id" in data:
            return {
                "status": "queued",
                "request_id": data["request_id"],
                "model": "flux-dev",
            }

        images = data.get("images", [])
        return {
            "status": "completed",
            "model": "flux-dev",
            "image_url": images[0]["url"] if images else None,
        }
