"""Runtime language selection checks."""

from __future__ import annotations

from PySide6.QtWidgets import QPushButton, QWidget

from character_model_studio.ui.i18n import LanguageManager


def test_korean_language_selection_translates_existing_widget_and_persists(qtbot, tmp_path) -> None:
    root = QWidget()
    button = QPushButton("Projects", root)
    qtbot.addWidget(root)
    manager = LanguageManager(tmp_path / "settings.json")

    manager.set_language("ko")
    manager.apply(root)

    assert button.text() == "\ud504\ub85c\uc81d\ud2b8"
    assert LanguageManager(tmp_path / "settings.json").language == "ko"

    manager.set_language("en")
    manager.apply(root)
    assert button.text() == "Projects"
