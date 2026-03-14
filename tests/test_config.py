"""Verify config module loads without errors."""
import importlib


def test_config_loads_with_env_vars(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setenv("TELEGRAM_USER_ID", "123456")

    # Re-import to pick up monkeypatched env
    from src import config
    importlib.reload(config)

    assert config.ANTHROPIC_API_KEY == "test-key"
    assert config.TELEGRAM_BOT_TOKEN == "test-token"
    assert config.TELEGRAM_USER_ID == 123456
