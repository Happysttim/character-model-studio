"""Design-system token and fallback tests."""

from __future__ import annotations

from character_model_studio.ui.theme import TOKENS, application_stylesheet


def test_warm_palette_tokens_are_centralized() -> None:
    stylesheet = application_stylesheet()

    assert TOKENS.canvas_warm == "#F5E6D7"
    assert TOKENS.amber == "#F2A65A"
    assert 'QPushButton[navRole="item"]:focus' in stylesheet
    assert "purple" not in stylesheet.lower()
