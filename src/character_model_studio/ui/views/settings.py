"""Language selection workspace."""

from __future__ import annotations

from PySide6.QtWidgets import QComboBox, QLabel, QVBoxLayout, QWidget

from character_model_studio.ui.i18n import LanguageManager
from character_model_studio.ui.widgets.glass import GlassPanel


class SettingsWorkspace(QWidget):
    """Persist and apply the English/Korean language selection."""

    def __init__(self, manager: LanguageManager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        panel = GlassPanel("secondary", self)
        form = QVBoxLayout(panel)
        form.addWidget(QLabel("Application language", panel))
        selector = QComboBox(panel)
        selector.setObjectName("languageSelector")
        selector.addItem("English", "en")
        selector.addItem("Korean", "ko")
        selector.setCurrentIndex(0 if manager.language == "en" else 1)
        selector.currentIndexChanged.connect(
            lambda index: manager.set_language(str(selector.itemData(index)))
        )
        form.addWidget(selector)
        form.addWidget(QLabel("Language changes apply immediately.", panel))
        form.addStretch(1)
        layout.addWidget(panel, stretch=1)
