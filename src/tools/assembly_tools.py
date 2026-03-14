"""Assembly tools - FFmpeg concat, audio overlay, captions, export, Remotion render."""
import asyncio
import json
import logging
import time
from pathlib import Path

from src.config import MEDIA_OUTPUT_DIR
from src.tools.registry import tool

logger = logging.getLogger(__name__)


async def _run_ffmpeg(args: list[str]) -> tuple[int, str, str]:
    """Run FFmpeg command and return (returncode, stdout, stderr)."""
    proc = await asyncio.create_subprocess_exec(
        "ffmpeg", *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    return proc.returncode, stdout.decode(), stderr.decode()


@tool
async def ffmpeg_concat_scenes(scene_paths: list, output_filename: str = "") -> dict:
    """Concatenate multiple video scenes into one video using FFmpeg.
    scene_paths: List of file paths to video scenes in order
    output_filename: Output filename (auto-generated if empty)
    """
    output_dir = Path(MEDIA_OUTPUT_DIR) / "assembled"
    output_dir.mkdir(parents=True, exist_ok=True)

    if not output_filename:
        output_filename = f"concat_{int(time.time())}.mp4"
    output_path = output_dir / output_filename

    # Create concat file list
    concat_file = output_dir / f"concat_{int(time.time())}.txt"
    with open(concat_file, "w") as f:
        for path in scene_paths:
            f.write(f"file '{path}'\n")

    returncode, stdout, stderr = await _run_ffmpeg([
        "-y", "-f", "concat", "-safe", "0",
        "-i", str(concat_file),
        "-c", "copy",
        str(output_path),
    ])

    concat_file.unlink(missing_ok=True)

    if returncode != 0:
        return {"error": f"FFmpeg concat failed: {stderr[:300]}"}

    return {
        "status": "completed",
        "output_path": str(output_path),
        "scene_count": len(scene_paths),
    }


@tool
async def ffmpeg_add_audio(
    video_path: str, audio_path: str, output_filename: str = "", mix_volume: float = 0.3
) -> dict:
    """Add audio track to video (background music or voiceover overlay).
    video_path: Path to the video file
    audio_path: Path to the audio file to overlay
    output_filename: Output filename (auto-generated if empty)
    mix_volume: Volume of added audio relative to original (0.0-1.0)
    """
    output_dir = Path(MEDIA_OUTPUT_DIR) / "assembled"
    output_dir.mkdir(parents=True, exist_ok=True)

    if not output_filename:
        output_filename = f"audio_mix_{int(time.time())}.mp4"
    output_path = output_dir / output_filename

    returncode, stdout, stderr = await _run_ffmpeg([
        "-y",
        "-i", video_path,
        "-i", audio_path,
        "-filter_complex",
        f"[0:a]volume=1.0[v];[1:a]volume={mix_volume}[a];[v][a]amix=inputs=2:duration=first",
        "-c:v", "copy",
        str(output_path),
    ])

    if returncode != 0:
        return {"error": f"FFmpeg audio mix failed: {stderr[:300]}"}

    return {
        "status": "completed",
        "output_path": str(output_path),
    }


@tool
async def ffmpeg_burn_captions(
    video_path: str, srt_path: str, output_filename: str = "",
    font_size: int = 24, font_color: str = "white", outline_color: str = "black"
) -> dict:
    """Burn SRT captions into video using FFmpeg subtitles filter.
    video_path: Path to the video file
    srt_path: Path to the SRT subtitle file
    output_filename: Output filename (auto-generated if empty)
    font_size: Caption font size
    font_color: Caption text color
    outline_color: Caption outline color
    """
    output_dir = Path(MEDIA_OUTPUT_DIR) / "assembled"
    output_dir.mkdir(parents=True, exist_ok=True)

    if not output_filename:
        output_filename = f"captioned_{int(time.time())}.mp4"
    output_path = output_dir / output_filename

    # Escape special chars in path for FFmpeg filter
    safe_srt = str(srt_path).replace("'", "\\'").replace(":", "\\:")

    returncode, stdout, stderr = await _run_ffmpeg([
        "-y",
        "-i", video_path,
        "-vf", (
            f"subtitles='{safe_srt}'"
            f":force_style='FontSize={font_size},"
            f"PrimaryColour=&H00{_color_to_bgr(font_color)},"
            f"OutlineColour=&H00{_color_to_bgr(outline_color)},"
            f"Outline=2,Shadow=1,MarginV=40'"
        ),
        "-c:a", "copy",
        str(output_path),
    ])

    if returncode != 0:
        return {"error": f"FFmpeg caption burn failed: {stderr[:300]}"}

    return {
        "status": "completed",
        "output_path": str(output_path),
    }


def _color_to_bgr(color_name: str) -> str:
    """Convert color name to BGR hex for ASS subtitle format."""
    colors = {
        "white": "FFFFFF",
        "black": "000000",
        "yellow": "00FFFF",
        "red": "0000FF",
        "green": "00FF00",
        "blue": "FF0000",
    }
    return colors.get(color_name.lower(), "FFFFFF")


@tool
async def ffmpeg_export_formats(
    video_path: str, formats: list = None
) -> dict:
    """Export video in multiple platform-optimized formats.
    video_path: Path to the source video
    formats: List of target formats (tiktok, youtube_short, instagram_reel, youtube_long)
    """
    if formats is None:
        formats = ["tiktok", "youtube_short", "instagram_reel"]

    output_dir = Path(MEDIA_OUTPUT_DIR) / "exports"
    output_dir.mkdir(parents=True, exist_ok=True)

    format_specs = {
        "tiktok": {"width": 1080, "height": 1920, "max_duration": 180, "bitrate": "8M"},
        "youtube_short": {"width": 1080, "height": 1920, "max_duration": 60, "bitrate": "10M"},
        "instagram_reel": {"width": 1080, "height": 1920, "max_duration": 90, "bitrate": "8M"},
        "youtube_long": {"width": 1920, "height": 1080, "max_duration": 3600, "bitrate": "15M"},
    }

    results = {}
    for fmt in formats:
        spec = format_specs.get(fmt)
        if not spec:
            results[fmt] = {"error": f"Unknown format: {fmt}"}
            continue

        output_filename = f"{fmt}_{int(time.time())}.mp4"
        output_path = output_dir / output_filename

        returncode, stdout, stderr = await _run_ffmpeg([
            "-y",
            "-i", video_path,
            "-vf", f"scale={spec['width']}:{spec['height']}:force_original_aspect_ratio=decrease,"
                   f"pad={spec['width']}:{spec['height']}:(ow-iw)/2:(oh-ih)/2",
            "-b:v", spec["bitrate"],
            "-c:a", "aac", "-b:a", "192k",
            str(output_path),
        ])

        if returncode != 0:
            results[fmt] = {"error": stderr[:200]}
        else:
            results[fmt] = {"output_path": str(output_path)}

    return {"exports": results}


@tool
async def remotion_render(
    composition_id: str, props: dict = None, output_filename: str = ""
) -> dict:
    """Render motion graphics video using Remotion CLI.
    composition_id: Remotion composition ID to render
    props: Input props JSON for the composition
    output_filename: Output filename (auto-generated if empty)
    """
    output_dir = Path(MEDIA_OUTPUT_DIR) / "remotion"
    output_dir.mkdir(parents=True, exist_ok=True)

    if not output_filename:
        output_filename = f"remotion_{composition_id}_{int(time.time())}.mp4"
    output_path = output_dir / output_filename

    cmd = [
        "npx", "remotion", "render",
        composition_id,
        str(output_path),
    ]

    if props:
        cmd.extend(["--props", json.dumps(props)])

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()

    if proc.returncode != 0:
        return {"error": f"Remotion render failed: {stderr.decode()[:300]}"}

    return {
        "status": "completed",
        "output_path": str(output_path),
        "composition": composition_id,
    }
