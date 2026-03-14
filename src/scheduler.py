"""Scheduler - JobQueue-based scheduled tasks for briefings and alerts."""
import logging
from datetime import time

from telegram.ext import Application, ContextTypes

from src.config import TELEGRAM_USER_ID
from src.agents.researcher import run_morning_briefing, run_trend_scan
from src.agents.orchestrator import chat

logger = logging.getLogger(__name__)

# Eastern Time schedule (UTC offsets)
# EST = UTC-5, EDT = UTC-4
# Using UTC times that correspond to target EST times
MORNING_BRIEFING_UTC = time(hour=13, minute=0)  # 8 AM EST / 9 AM EDT
TRENDING_ALERT_UTC = time(hour=17, minute=0)     # 12 PM EST / 1 PM EDT
HEALTH_CHECK_UTC = time(hour=19, minute=0)       # 2 PM EST / 3 PM EDT


async def _send_to_jah(context: ContextTypes.DEFAULT_TYPE, text: str) -> None:
    """Send a message to JAH's Telegram chat."""
    # Split long messages
    if len(text) > 4000:
        chunks = [text[i:i + 4000] for i in range(0, len(text), 4000)]
        for chunk in chunks:
            await context.bot.send_message(
                chat_id=TELEGRAM_USER_ID,
                text=chunk,
                parse_mode="Markdown",
            )
    else:
        await context.bot.send_message(
            chat_id=TELEGRAM_USER_ID,
            text=text,
            parse_mode="Markdown",
        )


async def morning_briefing_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Daily 8 AM morning briefing."""
    logger.info("Running scheduled morning briefing...")
    try:
        briefing = await run_morning_briefing()
        await _send_to_jah(context, briefing)
        logger.info("Morning briefing sent successfully")
    except Exception as e:
        logger.error(f"Morning briefing failed: {e}", exc_info=True)
        await _send_to_jah(context, f"Morning briefing failed: {e}")


async def trending_alert_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Daily noon trending topic alert."""
    logger.info("Running trending scan...")
    try:
        trends = await run_trend_scan()
        await _send_to_jah(context, trends)
    except Exception as e:
        logger.error(f"Trending scan failed: {e}", exc_info=True)


async def health_check_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Mon/Wed/Fri 2 PM pipeline health check."""
    logger.info("Running scheduled health check...")
    try:
        health = await chat(
            "Quick pipeline health check - items per status, any blockers, "
            "and what should I focus on today?"
        )
        await _send_to_jah(context, health)
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)


def setup_scheduled_jobs(app: Application) -> None:
    """Register all scheduled jobs with the bot's JobQueue."""
    job_queue = app.job_queue

    # Daily morning briefing at 8 AM EST
    job_queue.run_daily(
        morning_briefing_job,
        time=MORNING_BRIEFING_UTC,
        name="morning_briefing",
    )

    # Daily trending alert at noon EST
    job_queue.run_daily(
        trending_alert_job,
        time=TRENDING_ALERT_UTC,
        name="trending_alert",
    )

    # Mon/Wed/Fri health check at 2 PM EST
    job_queue.run_daily(
        health_check_job,
        time=HEALTH_CHECK_UTC,
        days=(0, 2, 4),  # Monday, Wednesday, Friday
        name="health_check",
    )

    logger.info(
        "Scheduled jobs registered: morning_briefing (daily 8am EST), "
        "trending_alert (daily 12pm EST), health_check (MWF 2pm EST)"
    )
