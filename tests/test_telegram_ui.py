"""Test Telegram UI helpers."""
from src.telegram_ui import approval_keyboard, idea_keyboard, hook_selection_keyboard


def test_approval_keyboard_has_3_buttons():
    kb = approval_keyboard("item-123")
    buttons = [btn for row in kb.inline_keyboard for btn in row]
    assert len(buttons) == 3
    assert buttons[0].callback_data == "approve:item-123"
    assert buttons[1].callback_data == "reject:item-123"
    assert buttons[2].callback_data == "develop:item-123"


def test_idea_keyboard_has_3_buttons():
    kb = idea_keyboard("idea-456")
    buttons = [btn for row in kb.inline_keyboard for btn in row]
    assert len(buttons) == 3
    assert buttons[0].callback_data == "develop:idea-456"


def test_hook_selection_keyboard_labels():
    hooks = [
        {"id": "h1", "text": "This hook grabs attention immediately"},
        {"id": "h2", "text": "Another powerful opening line here", "contrarian": True},
    ]
    kb = hook_selection_keyboard(hooks)
    buttons = [btn for row in kb.inline_keyboard for btn in row]
    assert len(buttons) == 2
    assert "A:" in buttons[0].text
    assert "(Contrarian)" in buttons[1].text
    assert buttons[1].callback_data == "hook:h2"
