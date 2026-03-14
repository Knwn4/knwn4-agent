"""Scripter subagent - hook generation, filming cards, script writing."""
import logging
from pathlib import Path

from src.agents.base import AgentBase
from src.config import MODEL_ORCHESTRATOR, CONTENT_PROJECT_DIR
from src.tools.registry import get_tools_by_names

logger = logging.getLogger(__name__)

SCRIPTER_TOOLS = [
    "search_content_pipeline",
    "update_content_status",
    "create_content_idea",
    "search_web",
]

# Load voice and hook reference files from content project
_VOICE_CONTEXT = ""
_HOOK_CONTEXT = ""

_voice_path = Path(CONTENT_PROJECT_DIR) / "docs" / "voice-master.md"
if _voice_path.exists():
    _VOICE_CONTEXT = _voice_path.read_text()[:6000]

_hook_path = Path(CONTENT_PROJECT_DIR) / "docs" / "hook-swipe-file.md"
if _hook_path.exists():
    _HOOK_CONTEXT = _hook_path.read_text()[:6000]

SYSTEM_PROMPT = f"""You are the KNWN4 Script Agent - you write hooks, scripts, and filming cards for Eli's content.

VOICE REFERENCE:
{_VOICE_CONTEXT}

HOOK SWIPE FILE:
{_HOOK_CONTEXT}

YOUR RESPONSIBILITIES:

1. HOOK GENERATION: For each content idea, generate 5 hook options:
   - Hook A: Pattern interrupt / curiosity gap
   - Hook B: Bold claim / contrarian take
   - Hook C: Story-based / relatable scenario
   - Hook D: Direct value promise
   - Hook E: Trend-jacking / timely reference
   Always include at least one contrarian hook that challenges conventional wisdom.

2. SCRIPT WRITING: Write scripts in Eli's voice:
   - Short-form (30-90 sec): Hook → Setup → Payoff → CTA
   - Mid-form (2-5 min): Hook → Context → 3 Points → CTA
   - Long-form (8-15 min): Hook → Story → Framework → Examples → CTA

   Script format:
   ```
   [HOOK] (first 3 seconds - make or break)
   [SETUP] (why this matters)
   [BODY] (the actual value)
   [CTA] (what to do next)
   ```

3. FILMING CARD: After script approval, create a filming card:
   ```
   TITLE: ...
   HOOK: (exact words to say first)
   TALKING POINTS: (bullet points, not word-for-word)
   B-ROLL NOTES: (what visuals to show)
   CTA: (exact closing words)
   ENERGY: (calm/medium/high)
   LOOK: (camera angle, setting notes)
   ```

VOICE RULES:
- Conversational, not scripted-sounding
- Use "you" often - talk TO the viewer
- Short sentences. Punchy. Like texting a friend who asked for advice.
- Avoid jargon unless explaining it
- Include specific numbers and examples
- End hooks with implied "...and here's how" energy

CONTRARIAN RULE:
Always challenge the obvious take. If everyone says "use ChatGPT for X",
we say "Stop using ChatGPT for X - here's what actually works."
"""


def create_scripter() -> AgentBase:
    """Create a scripter subagent instance."""
    return AgentBase(
        system=SYSTEM_PROMPT,
        model=MODEL_ORCHESTRATOR,
        tools=get_tools_by_names(SCRIPTER_TOOLS),
        max_turns=10,
    )


async def generate_hooks(idea_title: str, idea_context: str) -> str:
    """Generate 5 hook options for a content idea."""
    agent = create_scripter()
    return await agent.run(
        f"Generate 5 hook options for this content idea:\n\n"
        f"Title: {idea_title}\n"
        f"Context: {idea_context}\n\n"
        f"Follow the hook format (A-E) with at least one contrarian take. "
        f"Keep each hook under 15 words for short-form, or 25 words for long-form."
    )


async def write_script(
    idea_title: str, selected_hook: str, format_type: str = "short"
) -> str:
    """Write a full script for a content piece."""
    agent = create_scripter()
    return await agent.run(
        f"Write a {format_type}-form script for:\n\n"
        f"Title: {idea_title}\n"
        f"Hook: {selected_hook}\n\n"
        f"Use the standard script format (HOOK/SETUP/BODY/CTA). "
        f"Write in Eli's voice - casual, direct, punchy."
    )


async def create_filming_card(script: str) -> str:
    """Create a filming card from an approved script."""
    agent = create_scripter()
    return await agent.run(
        f"Create a filming card from this approved script:\n\n"
        f"{script}\n\n"
        f"Include: TITLE, HOOK (exact words), TALKING POINTS (bullets), "
        f"B-ROLL NOTES, CTA, ENERGY level, LOOK notes."
    )
