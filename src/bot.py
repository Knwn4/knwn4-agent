"""Telegram bot setup and configuration."""
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from src.config import TELEGRAM_BOT_TOKEN, TELEGRAM_USER_ID
from src.handlers.commands import (
    handle_start,
    handle_text,
    handle_status,
    handle_reset,
    handle_briefing,
)
from src.handlers.callbacks import handle_approval_callback


# Security: only JAH can talk to this bot
WHITELIST_FILTER = filters.User(user_id=[TELEGRAM_USER_ID])


def build_app() -> Application:
    """Build and configure the Telegram bot application."""
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Command handlers (whitelisted)
    app.add_handler(CommandHandler("start", handle_start, filters=WHITELIST_FILTER))
    app.add_handler(CommandHandler("status", handle_status, filters=WHITELIST_FILTER))
    app.add_handler(CommandHandler("reset", handle_reset, filters=WHITELIST_FILTER))
    app.add_handler(CommandHandler("briefing", handle_briefing, filters=WHITELIST_FILTER))

    # Callback query handler for inline buttons
    app.add_handler(CallbackQueryHandler(
        handle_approval_callback,
        pattern=r"^(approve|reject|develop|skip|star):",
    ))

    # Free-text handler (whitelisted) - must be last
    app.add_handler(MessageHandler(
        WHITELIST_FILTER & filters.TEXT & ~filters.COMMAND,
        handle_text,
    ))

    return app
