"""KNWN4 Content Agent — entry point."""
import logging

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def main() -> None:
    from src.config import TELEGRAM_BOT_TOKEN, ANTHROPIC_API_KEY

    missing = []
    if not TELEGRAM_BOT_TOKEN:
        missing.append("TELEGRAM_BOT_TOKEN")
    if not ANTHROPIC_API_KEY:
        missing.append("ANTHROPIC_API_KEY")
    if missing:
        raise RuntimeError(f"Missing required env vars: {', '.join(missing)}")

    from src.tools import register_all_tools
    from src.bot import build_app
    from src.scheduler import setup_scheduled_jobs

    # Register all tools before building bot
    register_all_tools()

    logger.info("KNWN4 Content Agent starting...")
    app = build_app()

    # Setup scheduled jobs (morning briefing, trending alerts, health checks)
    setup_scheduled_jobs(app)

    logger.info("Bot built with scheduled jobs. Starting polling...")
    app.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()
