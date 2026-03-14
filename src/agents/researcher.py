"""Researcher subagent - morning briefings, competitor scanning, trend detection."""
import logging

from src.agents.base import AgentBase
from src.config import MODEL_WORKER, CONTENT_PROJECT_DIR
from src.tools.registry import get_tools_by_names

logger = logging.getLogger(__name__)

RESEARCHER_TOOLS = [
    "search_web",
    "search_github_repos",
    "scan_competitors",
    "check_claude_updates",
    "check_openclaw_updates",
    "search_content_pipeline",
    "get_pipeline_health",
]

SYSTEM_PROMPT = """You are the KNWN4 Research Agent - you handle all research tasks for Eli's content pipeline.

Your responsibilities:
1. MORNING BRIEFING: Compile daily research report with:
   - Pipeline status (items per stage)
   - Top 3 ideas to develop today (highest potential)
   - AI news (Claude, OpenAI, Google AI, open-source)
   - Competitor activity (recent posts, view counts, hooks used)
   - GitHub updates (Claude Code, OpenClaw, MCP servers)

2. TREND DETECTION: Monitor for viral opportunities:
   - Breaking AI tool releases
   - Trending topics on AI Twitter/X
   - New open-source projects gaining stars
   - Competitor content gaps

3. COMPETITOR SCANNING: Track competitor content for:
   - Hook patterns that get high engagement
   - Topics they're covering (and missing)
   - Posting frequency and timing
   - Production style changes

COMPETITORS TO TRACK: drakesurach, ganonmeyer, aialchemyhub, mattvidpro, theaiadvantage

FORMAT: Always structure output with clear sections, bullet points, and actionable insights.
Be concise - Eli reviews this on mobile via Telegram.

SCORING: When presenting ideas, score them 1-10 based on:
- Trend momentum (is this topic rising?)
- Audience fit (does KNWN4 audience care?)
- Production feasibility (can we make this quickly?)
- Uniqueness (are competitors NOT covering this?)
"""


def create_researcher() -> AgentBase:
    """Create a researcher subagent instance."""
    return AgentBase(
        system=SYSTEM_PROMPT,
        model=MODEL_WORKER,
        tools=get_tools_by_names(RESEARCHER_TOOLS),
        max_turns=15,
    )


async def run_morning_briefing() -> str:
    """Run the full morning briefing research flow."""
    agent = create_researcher()
    return await agent.run(
        "Run the full morning briefing:\n"
        "1. Check pipeline health\n"
        "2. Find the top 3 ideas to develop today\n"
        "3. Check for AI news and Claude/OpenClaw updates\n"
        "4. Scan competitor activity\n"
        "5. Compile everything into a clean briefing format for Telegram"
    )


async def run_trend_scan() -> str:
    """Run a quick trend scan for timely content opportunities."""
    agent = create_researcher()
    return await agent.run(
        "Do a quick trend scan:\n"
        "1. Search for breaking AI news in the last 24 hours\n"
        "2. Check GitHub trending repos in AI/ML\n"
        "3. Look for viral AI content opportunities\n"
        "Return the top 3 most timely opportunities with why they'd work for KNWN4."
    )
