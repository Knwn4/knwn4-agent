"""Reusable Telegram UI components - keyboards, media senders, progress."""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatAction
from telegram.ext import ContextTypes


def approval_keyboard(item_id: str) -> InlineKeyboardMarkup:
    """Standard approve/reject/develop keyboard."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Approve", callback_data=f"approve:{item_id}"),
            InlineKeyboardButton("Reject", callback_data=f"reject:{item_id}"),
        ],
        [
            InlineKeyboardButton("Develop", callback_data=f"develop:{item_id}"),
        ],
    ])


def idea_keyboard(item_id: str) -> InlineKeyboardMarkup:
    """Idea review keyboard - develop, skip, or star."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Develop", callback_data=f"develop:{item_id}"),
            InlineKeyboardButton("Skip", callback_data=f"skip:{item_id}"),
            InlineKeyboardButton("Star", callback_data=f"star:{item_id}"),
        ],
    ])


def hook_selection_keyboard(hooks: list[dict]) -> InlineKeyboardMarkup:
    """Dynamic hook selection keyboard from a list of hooks."""
    labels = "ABCDEFGHIJ"
    buttons = []
    for i, hook in enumerate(hooks):
        label = labels[i] if i < len(labels) else str(i + 1)
        tag = " (Contrarian)" if hook.get("contrarian") else ""
        buttons.append([InlineKeyboardButton(
            f"{label}{tag}: {hook['text'][:40]}...",
            callback_data=f"hook:{hook['id']}",
        )])
    return InlineKeyboardMarkup(buttons)


async def send_typing(context: ContextTypes.DEFAULT_TYPE, chat_id: int) -> None:
    """Send typing indicator."""
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)


async def send_image_for_review(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    image_path_or_url: str,
    item_id: str,
    caption: str,
) -> None:
    """Send image with approval keyboard attached."""
    if image_path_or_url.startswith("http"):
        await context.bot.send_photo(
            chat_id=chat_id,
            photo=image_path_or_url,
            caption=caption,
            reply_markup=approval_keyboard(item_id),
            parse_mode="Markdown",
        )
    else:
        with open(image_path_or_url, "rb") as f:
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=f,
                caption=caption,
                reply_markup=approval_keyboard(item_id),
                parse_mode="Markdown",
            )


async def send_video_for_review(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    video_path_or_url: str,
    item_id: str,
    caption: str,
) -> None:
    """Send video with approval keyboard attached."""
    if video_path_or_url.startswith("http"):
        await context.bot.send_video(
            chat_id=chat_id,
            video=video_path_or_url,
            caption=caption,
            reply_markup=approval_keyboard(item_id),
            parse_mode="Markdown",
        )
    else:
        with open(video_path_or_url, "rb") as f:
            await context.bot.send_video(
                chat_id=chat_id,
                video=f,
                caption=caption,
                reply_markup=approval_keyboard(item_id),
                parse_mode="Markdown",
            )


class ProgressMessage:
    """Editable progress message - updates in place."""

    def __init__(self, context: ContextTypes.DEFAULT_TYPE, chat_id: int):
        self._context = context
        self._chat_id = chat_id
        self._message = None

    async def start(self, text: str) -> None:
        self._message = await self._context.bot.send_message(
            chat_id=self._chat_id, text=text
        )

    async def update(self, text: str) -> None:
        if self._message:
            await self._message.edit_text(text)

    async def finish(self, text: str, reply_markup=None) -> None:
        if self._message:
            await self._message.edit_text(text, reply_markup=reply_markup)
