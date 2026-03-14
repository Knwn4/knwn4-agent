"""Publisher subagent - calendar management, platform formatting, Notion updates."""
import logging

from src.agents.base import AgentBase
from src.config import MODEL_WORKER, N8N_BASE_URL, N8N_API_KEY
from src.tools.registry import get_tools_by_names, tool

logger = logging.getLogger(__name__)

PUBLISHER_TOOLS = [
    "search_content_pipeline",
    "get_pipeline_health",
    "update_content_status",
    "log_automation_action",
    "trigger_n8n_workflow",
    "format_for_platform",
]

SYSTEM_PROMPT = """You are the KNWN4 Publisher Agent - you handle scheduling, platform formatting, and status management.

YOUR RESPONSIBILITIES:

1. CALENDAR MANAGEMENT:
   - Track posting schedule (optimal times per platform)
   - Ensure balanced content pillar distribution per week
   - Flag scheduling conflicts or gaps
   - Suggested schedule:
     * TikTok: Daily 11am, 3pm, 7pm EST
     * YouTube Shorts: Daily 12pm, 5pm EST
     * Instagram Reels: Daily 10am, 2pm, 6pm EST
     * YouTube Long: Tue/Thu/Sat 8am EST

2. PLATFORM FORMATTING:
   - Adapt captions/descriptions per platform
   - Add relevant hashtags
   - Format CTAs for each platform's style
   - Generate thumbnail text variants

3. STATUS UPDATES:
   - Move content through pipeline stages
   - Log all publishing actions
   - Track publishing confirmations

4. N8N INTEGRATION:
   - Trigger publishing workflows
   - Monitor workflow execution
   - Handle failures gracefully

FORMATTING RULES:
- TikTok: Short caption, trending hashtags, hook in first line
- YouTube Shorts: SEO title, description with keywords, relevant tags
- Instagram Reels: Caption with line breaks, branded hashtags, CTA
- YouTube Long: Full description, timestamps, links, tags
"""


# --- Publisher-specific tools ---

@tool
async def trigger_n8n_workflow(workflow_id: str, payload: dict = None) -> dict:
    """Trigger an n8n workflow for publishing or other automation.
    workflow_id: The n8n workflow ID to trigger
    payload: JSON payload to send to the workflow
    """
    import httpx

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{N8N_BASE_URL}/api/v1/workflows/{workflow_id}/activate",
            headers={"Authorization": f"Bearer {N8N_API_KEY}"},
            json=payload or {},
            timeout=30.0,
        )
        response.raise_for_status()
        return {"status": "triggered", "workflow_id": workflow_id}


@tool
def format_for_platform(title: str, description: str, platform: str, hashtags: list = None) -> dict:
    """Format content metadata for a specific platform.
    title: Content title
    description: Content description/script summary
    platform: Target platform (tiktok, youtube_shorts, instagram_reels, youtube_long)
    hashtags: List of hashtags to include
    """
    if hashtags is None:
        hashtags = ["#ai", "#automation", "#aitools", "#tech"]

    formatters = {
        "tiktok": _format_tiktok,
        "youtube_shorts": _format_youtube_shorts,
        "instagram_reels": _format_instagram_reels,
        "youtube_long": _format_youtube_long,
    }

    formatter = formatters.get(platform)
    if not formatter:
        return {"error": f"Unknown platform: {platform}"}

    return formatter(title, description, hashtags)


def _format_tiktok(title: str, description: str, hashtags: list) -> dict:
    tag_str = " ".join(hashtags[:10])
    caption = f"{title}\n\n{description[:100]}\n\n{tag_str}"
    return {"platform": "tiktok", "caption": caption[:2200]}


def _format_youtube_shorts(title: str, description: str, hashtags: list) -> dict:
    tag_str = " ".join(hashtags[:15])
    return {
        "platform": "youtube_shorts",
        "title": title[:100],
        "description": f"{description}\n\n{tag_str}\n\n#shorts",
        "tags": hashtags,
    }


def _format_instagram_reels(title: str, description: str, hashtags: list) -> dict:
    tag_str = " ".join(hashtags[:30])
    caption = f"{title}\n\n{description[:500]}\n\n.\n.\n.\n{tag_str}"
    return {"platform": "instagram_reels", "caption": caption[:2200]}


def _format_youtube_long(title: str, description: str, hashtags: list) -> dict:
    return {
        "platform": "youtube_long",
        "title": title[:100],
        "description": (
            f"{description}\n\n"
            f"---\n"
            f"Follow KNWN4:\n"
            f"TikTok: @knwn4\n"
            f"Instagram: @knwn4\n\n"
            f"{' '.join(hashtags[:15])}"
        ),
        "tags": hashtags,
    }


def create_publisher() -> AgentBase:
    """Create a publisher subagent instance."""
    return AgentBase(
        system=SYSTEM_PROMPT,
        model=MODEL_WORKER,
        tools=get_tools_by_names(PUBLISHER_TOOLS),
        max_turns=10,
    )


async def schedule_content(content_id: str, title: str, platforms: list) -> str:
    """Schedule content for publishing across platforms."""
    agent = create_publisher()
    platform_str = ", ".join(platforms)
    return await agent.run(
        f"Schedule this content for publishing:\n\n"
        f"Content ID: {content_id}\n"
        f"Title: {title}\n"
        f"Platforms: {platform_str}\n\n"
        f"1. Format metadata for each platform\n"
        f"2. Pick optimal posting times\n"
        f"3. Update content status to 'Scheduled'\n"
        f"4. Log the scheduling action"
    )


async def publish_now(content_id: str, platform: str, workflow_id: str) -> str:
    """Publish content immediately via n8n workflow."""
    agent = create_publisher()
    return await agent.run(
        f"Publish content now:\n\n"
        f"Content ID: {content_id}\n"
        f"Platform: {platform}\n"
        f"Workflow ID: {workflow_id}\n\n"
        f"1. Trigger the n8n publishing workflow\n"
        f"2. Update status to 'Published'\n"
        f"3. Log the action"
    )
