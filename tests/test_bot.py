"""Test bot setup and handler registration."""
import importlib


def test_build_app_registers_handlers(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test:token")
    monkeypatch.setenv("TELEGRAM_USER_ID", "123")

    from src import config
    importlib.reload(config)
    from src import bot
    importlib.reload(bot)
    from src.bot import build_app

    app = build_app()
    # Should have at least 4 handlers: start, status, callback, text
    assert len(app.handlers[0]) >= 4
