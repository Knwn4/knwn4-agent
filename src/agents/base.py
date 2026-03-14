"""Base agent with agentic loop - handles tool_use cycling."""
import logging
from typing import Optional
from anthropic import Anthropic
from anthropic.types import TextBlock, ToolUseBlock

from src.config import ANTHROPIC_API_KEY, MAX_TOKENS_DEFAULT, MAX_AGENTIC_TURNS
from src.tools.registry import run_tool

logger = logging.getLogger(__name__)

_client: Optional[Anthropic] = None


def get_client() -> Anthropic:
    """Lazy-init Anthropic client."""
    global _client
    if _client is None:
        _client = Anthropic(api_key=ANTHROPIC_API_KEY)
    return _client


class AgentBase:
    """Base agent with agentic tool_use loop.

    Subclass and override `system_prompt` and `tool_names` for specialized agents.
    """

    def __init__(
        self,
        system: str,
        model: str,
        tools: list[dict],
        max_turns: int = MAX_AGENTIC_TURNS,
    ):
        self.system = system
        self.model = model
        self.tools = tools
        self.max_turns = max_turns
        self.messages: list[dict] = []

    async def run(self, user_message: str) -> str:
        """Run the agentic loop with a user message. Returns final text response."""
        self.messages.append({"role": "user", "content": user_message})

        client = get_client()

        for turn in range(self.max_turns):
            logger.info(f"Agent turn {turn + 1}/{self.max_turns} (model={self.model})")

            response = client.messages.create(
                model=self.model,
                max_tokens=MAX_TOKENS_DEFAULT,
                system=self.system,
                tools=self.tools,
                messages=self.messages,
            )

            self.messages.append({"role": "assistant", "content": response.content})

            # Check for final text response
            if response.stop_reason == "end_turn":
                text_parts = [
                    block.text for block in response.content
                    if isinstance(block, TextBlock)
                ]
                return "\n".join(text_parts) if text_parts else "(No text response)"

            # Handle tool calls
            if response.stop_reason == "tool_use":
                tool_results = []
                for block in response.content:
                    if isinstance(block, ToolUseBlock):
                        logger.info(f"Tool call: {block.name}({block.input})")
                        result = await run_tool(block.name, block.input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result,
                        })

                self.messages.append({"role": "user", "content": tool_results})
            else:
                logger.warning(f"Unexpected stop_reason: {response.stop_reason}")
                break

        return "(Agent reached max turns without completing)"

    def reset(self) -> None:
        """Clear conversation history."""
        self.messages.clear()
