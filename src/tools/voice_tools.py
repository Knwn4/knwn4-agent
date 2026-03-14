"""Voice tools - ElevenLabs TTS with JAH voice clone + masked voice variant."""
import logging
import os
from pathlib import Path

import httpx

from src.config import ELEVENLABS_API_KEY, MEDIA_OUTPUT_DIR
from src.tools.registry import tool

logger = logging.getLogger(__name__)

# JAH's cloned voice ID (set in ElevenLabs dashboard)
JAH_VOICE_ID = os.environ.get("ELEVENLABS_JAH_VOICE_ID", "")

# Default voice settings for JAH
JAH_VOICE_SETTINGS = {
    "stability": 0.5,
    "similarity_boost": 0.75,
    "style": 0.3,
    "use_speaker_boost": True,
}


@tool
async def generate_voiceover_jah(text: str, output_filename: str = "") -> dict:
    """Generate voiceover in JAH's cloned voice via ElevenLabs.
    text: The script text to convert to speech
    output_filename: Optional output filename (auto-generated if empty)
    """
    if not JAH_VOICE_ID:
        return {"error": "ELEVENLABS_JAH_VOICE_ID not configured"}

    output_dir = Path(MEDIA_OUTPUT_DIR) / "voiceovers"
    output_dir.mkdir(parents=True, exist_ok=True)

    if not output_filename:
        import time
        output_filename = f"jah_vo_{int(time.time())}.mp3"
    output_path = output_dir / output_filename

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{JAH_VOICE_ID}",
            headers={
                "xi-api-key": ELEVENLABS_API_KEY,
                "Content-Type": "application/json",
            },
            json={
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": JAH_VOICE_SETTINGS,
            },
            timeout=60.0,
        )
        response.raise_for_status()

        output_path.write_bytes(response.content)

    return {
        "status": "completed",
        "voice": "jah",
        "output_path": str(output_path),
        "text_length": len(text),
    }


@tool
async def generate_voiceover_mask(
    text: str, pitch_shift: float = -3.0, output_filename: str = ""
) -> dict:
    """Generate masked/altered voiceover - JAH voice with FFmpeg pitch processing.
    text: The script text to convert to speech
    pitch_shift: Semitones to shift pitch (negative = deeper, e.g. -3.0)
    output_filename: Optional output filename (auto-generated if empty)
    """
    if not JAH_VOICE_ID:
        return {"error": "ELEVENLABS_JAH_VOICE_ID not configured"}

    output_dir = Path(MEDIA_OUTPUT_DIR) / "voiceovers"
    output_dir.mkdir(parents=True, exist_ok=True)

    import time
    timestamp = int(time.time())
    raw_filename = f"mask_raw_{timestamp}.mp3"
    raw_path = output_dir / raw_filename

    if not output_filename:
        output_filename = f"mask_vo_{timestamp}.mp3"
    output_path = output_dir / output_filename

    # Step 1: Generate base voiceover
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{JAH_VOICE_ID}",
            headers={
                "xi-api-key": ELEVENLABS_API_KEY,
                "Content-Type": "application/json",
            },
            json={
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.4,
                    "similarity_boost": 0.6,
                    "style": 0.5,
                    "use_speaker_boost": False,
                },
            },
            timeout=60.0,
        )
        response.raise_for_status()
        raw_path.write_bytes(response.content)

    # Step 2: Apply pitch shift with FFmpeg
    import asyncio

    # Calculate asetrate for pitch shift (semitones to frequency ratio)
    ratio = 2 ** (pitch_shift / 12.0)
    new_rate = int(44100 * ratio)

    proc = await asyncio.create_subprocess_exec(
        "ffmpeg", "-y",
        "-i", str(raw_path),
        "-af", f"asetrate={new_rate},aresample=44100",
        str(output_path),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()

    if proc.returncode != 0:
        logger.error(f"FFmpeg pitch shift failed: {stderr.decode()}")
        return {"error": f"FFmpeg failed: {stderr.decode()[:200]}"}

    # Cleanup raw file
    raw_path.unlink(missing_ok=True)

    return {
        "status": "completed",
        "voice": "masked",
        "pitch_shift": pitch_shift,
        "output_path": str(output_path),
        "text_length": len(text),
    }
