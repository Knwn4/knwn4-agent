"""Inline keyboard callback handlers for approval flows."""
import logging
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


async def handle_approval_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline button presses (approve/reject/develop/skip/star)."""
    query = update.callback_query
    await query.answer()

    action, item_id = query.data.split(":", 1)
    logger.info(f"Callback: {action} on {item_id}")

    responses = {
        "approve": f"Approved: {item_id}",
        "reject": f"Rejected: {item_id}",
        "develop": f"Developing: {item_id}...",
        "skip": f"Skipped: {item_id}",
        "star": f"Starred: {item_id}",
    }

    await query.edit_message_text(
        responses.get(action, f"Unknown action: {action}")
    )
    # Downstream automation will be connected in Phase 3
