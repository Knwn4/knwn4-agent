"""Telegram command and message handlers."""
import logging
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ContextTypes

from src.agents.orchestrator import chat, reset_agent

logger = logging.getLogger(__name__)


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    reset_agent()
    await update.message.reply_text(
        "KNWN4 Content Agent is live.\n\n"
        "Commands:\n"
        "/status - Pipeline health check\n"
        "/reset - Start fresh conversation\n"
        "/briefing - Get morning briefing now\n\n"
        "Or just message me anything."
    )


async def handle_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /status command."""
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, action=ChatAction.TYPING
    )
    response = await chat("Give me a quick pipeline health check - how many items in each status?")
    await update.message.reply_text(response, parse_mode="Markdown")


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle free-text messages - route to orchestrator agent."""
    text = update.message.text
    chat_id = update.effective_chat.id
    logger.info(f"Message from JAH: {text}")

    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

    try:
        response = await chat(text)

        # Telegram has a 4096 char limit per message
        if len(response) > 4000:
            chunks = [response[i:i + 4000] for i in range(0, len(response), 4000)]
            for chunk in chunks:
                await update.message.reply_text(chunk, parse_mode="Markdown")
        else:
            await update.message.reply_text(response, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Orchestrator error: {e}", exc_info=True)
        await update.message.reply_text(f"Error: {e}")


async def handle_reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /reset command - clear conversation state."""
    reset_agent()
    await update.message.reply_text("Conversation reset. Fresh start.")


async def handle_briefing(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /briefing command - trigger morning briefing now."""
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, action=ChatAction.TYPING
    )
    response = await chat(
        "Run the morning briefing now: pipeline status, top ideas to develop, "
        "AI news, and competitor moves."
    )
    await update.message.reply_text(response, parse_mode="Markdown")
