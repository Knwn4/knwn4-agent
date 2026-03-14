"""Telegram command and message handlers."""
import logging
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    await update.message.reply_text(
        "KNWN4 Content Agent is live.\n\n"
        "Commands:\n"
        "/status - Pipeline health check\n\n"
        "Or just message me anything - I'll route it to the right workflow."
    )


async def handle_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /status command - pipeline health check."""
    await update.message.reply_text("Checking pipeline... (agent integration pending)")


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle free-text messages - route to orchestrator agent."""
    text = update.message.text
    chat_id = update.effective_chat.id
    logger.info(f"Message from JAH: {text}")

    # Placeholder - will be replaced by orchestrator agent in Phase 2
    await update.message.reply_text(
        f"Received: \"{text}\"\n\n(Orchestrator agent not yet connected)"
    )
