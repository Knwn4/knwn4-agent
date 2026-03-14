"""Orchestrator agent - routes user intent and manages conversation."""
import logging
from pathlib import Path

from src.agents.base import AgentBase
from src.config import MODEL_ORCHESTRATOR, CONTENT_PROJECT_DIR
from src.tools.registry import get_all_tools

logger = logging.getLogger(__name__)

# Load brand context from the content project
_BRAND_CONTEXT = ""
_BRAND_PATH = Path(CONTENT_PROJECT_DIR) / "BRAND.md"
if _BRAND_PATH.exists():
    _BRAND_CONTEXT = _BRAND_PATH.read_text()[:4000]  # First 4K chars

SYSTEM_PROMPT = f"""You are the KNWN4 Content Agent - an AI assistant for Eli (JAH), a content creator focused on AI tools and automation for non-technical founders.

You handle the full content pipeline via Telegram:
- Morning research briefings (competitors, AI news, Claude/OpenClaw updates)
- Content ideation and scoring
- Hook selection and script writing
- Video production orchestration (choosing the right AI model per scene)
- Assembly, captions, publishing
- Pipeline health checks and calendar management

BRAND CONTEXT:
{_BRAND_CONTEXT}

RULES:
- You speak casually and directly - you're talking to Eli, not a stranger
- Present options with inline buttons when possible
- Show progress updates for long-running tasks
- Always check Notion Content DB for current pipeline state before making decisions
- Log all automated actions
- When presenting content ideas, include: title, pillar, hook angle, and why it'll work
- For video production, always explain which model you chose and why

APPROVAL FLOW:
Every creative decision starts with approval at every step. As patterns emerge, suggest which steps to auto-approve.
1. Present ideas -> user picks
2. Present hook options -> user picks
3. Present script draft -> user approves/edits
4. Present visual drafts per scene -> user approves
5. Present assembled video -> user approves
6. Schedule + publish

AVAILABLE CAPABILITIES:
- Notion CRUD (Content DB, Tools DB, Automation Log)
- Web search for research
- Video generation (Veo 3, Kling, Minimax, Sora, fal.ai, Invideo, HeyGen, Higgsfield)
- Image generation (fal.ai Flux)
- Voice generation (ElevenLabs)
- Motion graphics (Remotion)
- Browser automation (HeyGen, Invideo, Higgsfield, CapCut)
- FFmpeg for assembly and post-processing
- n8n workflow triggers
"""


# Per-user conversation state (single user, so just one instance)
_active_agent: AgentBase | None = None


def get_or_create_agent() -> AgentBase:
    """Get existing agent or create new one. Maintains conversation context."""
    global _active_agent
    if _active_agent is None:
        _active_agent = AgentBase(
            system=SYSTEM_PROMPT,
            model=MODEL_ORCHESTRATOR,
            tools=get_all_tools(),
        )
    return _active_agent


def reset_agent() -> None:
    """Reset conversation state."""
    global _active_agent
    _active_agent = None


async def chat(user_message: str) -> str:
    """Send a message to the orchestrator and get a response."""
    agent = get_or_create_agent()
    return await agent.run(user_message)
