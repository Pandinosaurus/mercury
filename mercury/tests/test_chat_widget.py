import mercury.chat.chat as chat_module
from mercury.chat.chat import Chat


def test_chat_default_height_preserves_natural_layout(monkeypatch):
    monkeypatch.setattr(chat_module, "display", lambda *_: None)
    monkeypatch.setattr(chat_module, "clear_output", lambda *_, **__: None)

    chat = Chat()

    assert chat.height == ""
    assert chat.vbox.layout.height is None
    assert chat.vbox.layout.overflow == "visible"
    assert "mljar-chat-container" in chat.vbox._dom_classes


def test_chat_height_sets_internal_scroll(monkeypatch):
    monkeypatch.setattr(chat_module, "display", lambda *_: None)
    monkeypatch.setattr(chat_module, "clear_output", lambda *_, **__: None)

    chat = Chat(height="600px")

    assert chat.height == "600px"
    assert chat.vbox.layout.height == "600px"
    assert chat.vbox.layout.overflow == "auto"


def test_chat_height_accepts_viewport_units(monkeypatch):
    monkeypatch.setattr(chat_module, "display", lambda *_: None)
    monkeypatch.setattr(chat_module, "clear_output", lambda *_, **__: None)

    chat = Chat(height="70vh")

    assert chat.height == "70vh"
    assert chat.vbox.layout.height == "70vh"
    assert chat.vbox.layout.overflow == "auto"
