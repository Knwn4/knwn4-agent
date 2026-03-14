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

    logger.info("KNWN4 Content Agent starting...")
    # Bot setup will be added in Task 1.2
    logger.info("All systems nominal. Bot ready.")


if __name__ == "__main__":
    main()
