"""Producer subagent - model selection, asset generation, assembly orchestration."""
import logging

from src.agents.base import AgentBase
from src.config import MODEL_ORCHESTRATOR
from src.tools.registry import get_tools_by_names

logger = logging.getLogger(__name__)

PRODUCER_TOOLS = [
    # Video generation
    "select_best_model",
    "generate_video_veo3",
    "generate_video_kling",
    "generate_video_minimax",
    "generate_video_sora",
    "generate_image_flux",
    # Browser-based generation
    "heygen_create_video",
    "invideo_create_video",
    "higgsfield_create_avatar",
    # Voice
    "generate_voiceover_jah",
    "generate_voiceover_mask",
    # Assembly
    "ffmpeg_concat_scenes",
    "ffmpeg_add_audio",
    "ffmpeg_burn_captions",
    "ffmpeg_export_formats",
    "remotion_render",
    # Captions
    "capcut_auto_captions",
    # Pipeline
    "update_content_status",
    "log_automation_action",
]

SYSTEM_PROMPT = """You are the KNWN4 Producer Agent - you handle all video production from script to final export.

YOUR WORKFLOW:

1. SCENE BREAKDOWN: Take the approved script/filming card and break it into scenes:
   - Each scene gets: duration, visual type, audio source, text overlay
   - Identify which scenes need: AI video, talking head, screen recording, B-roll, motion graphics

2. MODEL SELECTION: For each scene, pick the best AI model:
   - Cinematic B-roll (nature, city) → Veo 3 (fallback: Kling Pro)
   - Talking head → HeyGen (fallback: Higgsfield)
   - Product demo → Remotion + Playwright (fallback: screen capture)
   - Abstract/stylized → fal.ai Flux + Kling (fallback: Minimax)
   - AI avatar with expressions → Higgsfield (fallback: HeyGen)
   - Full AI video from prompt → Invideo (fallback: Sora)
   - Motion graphics → Remotion (fallback: FFmpeg drawtext)
   - Quick talking head at scale → HeyGen API (fallback: ElevenLabs + still)
   - Smooth portrait → Minimax/Hailuo (fallback: Kling Standard)
   - Surreal/creative → Sora (fallback: Veo 3)

   ALWAYS explain your model choice: "Using Veo 3 for this establishing shot because..."

3. ASSET GENERATION: Generate all assets per scene:
   - Queue video generations (they take time)
   - Generate voiceover for narrated sections
   - Create images for thumbnails or image-to-video inputs
   - Log each generation in automation log

4. ASSEMBLY: Once all assets are ready:
   - Concatenate scenes in order
   - Add voiceover/music
   - Generate and burn captions
   - Export in platform-specific formats

5. QUALITY CHECK: Before presenting to Eli:
   - Verify all scenes are present
   - Check audio sync
   - Confirm captions are accurate
   - Export in all required formats

PRODUCTION RULES:
- Always start with the cheapest/fastest model, upgrade if quality isn't sufficient
- For browser-based tools, check auth status first
- Log every generation attempt and result
- If a model fails, automatically try the fallback
- Present scene-by-scene progress to Eli via Telegram
"""


def create_producer() -> AgentBase:
    """Create a producer subagent instance."""
    return AgentBase(
        system=SYSTEM_PROMPT,
        model=MODEL_ORCHESTRATOR,
        tools=get_tools_by_names(PRODUCER_TOOLS),
        max_turns=25,
    )


async def produce_video(filming_card: str, content_id: str) -> str:
    """Run the full production pipeline for a video."""
    agent = create_producer()
    return await agent.run(
        f"Produce a video from this filming card:\n\n"
        f"{filming_card}\n\n"
        f"Content ID: {content_id}\n\n"
        f"Steps:\n"
        f"1. Break into scenes with model selection\n"
        f"2. Generate all assets\n"
        f"3. Assemble final video\n"
        f"4. Export for TikTok, YouTube Shorts, and Instagram Reels\n"
        f"5. Update content status to 'Edit'\n"
        f"6. Present results summary"
    )


async def generate_scene(scene_description: str, scene_type: str, duration: int = 5) -> str:
    """Generate a single scene using the best model for the type."""
    agent = create_producer()
    return await agent.run(
        f"Generate a single video scene:\n\n"
        f"Description: {scene_description}\n"
        f"Type: {scene_type}\n"
        f"Duration: {duration}s\n\n"
        f"Use select_best_model to pick the right model, then generate the asset."
    )
