"""Local runtime English/Korean translation for Qt Widgets."""
# ruff: noqa: E501

from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QAbstractButton, QComboBox, QLabel, QLineEdit, QWidget

_KO = {
    "Projects": "\ud504\ub85c\uc81d\ud2b8",
    "Capture": "\ucea1\ucc98",
    "Processing": "\ucc98\ub9ac",
    "Review": "\uac80\ud1a0",
    "Rig": "\ub9ac\uae45",
    "Animate": "\uc560\ub2c8\uba54\uc774\uc158",
    "Diagnostics": "\uc9c4\ub2e8",
    "Settings": "\uc124\uc815",
    "Create project": "\ud504\ub85c\uc81d\ud2b8 \ub9cc\ub4e4\uae30",
    "Open selected project": "\uc120\ud0dd\ud55c \ud504\ub85c\uc81d\ud2b8 \uc5f4\uae30",
    "Refresh projects": "\ud504\ub85c\uc81d\ud2b8 \uc0c8\ub85c\uace0\uce68",
    "Create Rig": "\ub9ac\uadf8 \ub9cc\ub4e4\uae30",
    "Refresh readiness": "\uc900\ube44 \uc0c1\ud0dc \uc0c8\ub85c\uace0\uce68",
    "Selected bone": "\uc120\ud0dd\ub41c \ubcf8",
    "Save From": "From \ud3ec\uc988 \uc800\uc7a5",
    "Save To": "To \ud3ec\uc988 \uc800\uc7a5",
    "Reset pose": "\ud3ec\uc988 \ucd08\uae30\ud654",
    "Swap": "\ud3ec\uc988 \uad50\uccb4",
    "Duration": "\uae38\uc774",
    "Loop preview": "\ubc18\ubcf5 \ubbf8\ub9ac\ubcf4\uae30",
    "Play": "\uc7ac\uc0dd",
    "Pause": "\uc77c\uc2dc \uc815\uc9c0",
    "Stop": "\uc815\uc9c0",
    "Save animation": "\uc560\ub2c8\uba54\uc774\uc158 \uc800\uc7a5",
    "Reduce motion": "\ubaa8\uc158 \uc904\uc774\uae30",
    "Copy diagnostics": "\uc9c4\ub2e8 \uc815\ubcf4 \ubcf5\uc0ac",
    "Open log folder": "\ub85c\uadf8 \ud3f4\ub354 \uc5f4\uae30",
    "Import existing GLB": "\uae30\uc874 GLB \ubd88\ub7ec\uc624\uae30",
    "Import existing video": "\uae30\uc874 \uc601\uc0c1 \ubd88\ub7ec\uc624\uae30",
    "Start recording": "\ub179\ud654 \uc2dc\uc791",
    "Application language": "\uc571 \uc5b8\uc5b4",
    "Language changes apply immediately.": "\uc5b8\uc5b4 \ubcc0\uacbd\uc740 \uc989\uc2dc \uc801\uc6a9\ub429\ub2c8\ub2e4.",
    "English": "\uc601\uc5b4",
    "Korean": "\ud55c\uad6d\uc5b4",
    "Choose the application language and local preferences.": "\uc571 \uc5b8\uc5b4\uc640 \ub85c\uceec \uc124\uc815\uc744 \uc120\ud0dd\ud569\ub2c8\ub2e4.",
    "Local creative work, kept on this device.": "\uc774 \uc7a5\uce58\uc5d0 \uc800\uc7a5\ub418\ub294 \ub85c\uceec \uc791\uc5c5\uc785\ub2c8\ub2e4.",
    "Record a clear character view when capture is configured.": "\ucea1\ucc98 \uc124\uc815 \ud6c4 \uce90\ub9ad\ud130 \uc7a5\uba74\uc744 \ub179\ud654\ud569\ub2c8\ub2e4.",
    "Follow real processing stages when a job is running.": "\uc791\uc5c5 \uc2e4\ud589 \uc911 \uc2e4\uc81c \ucc98\ub9ac \ub2e8\uacc4\ub97c \ud655\uc778\ud569\ub2c8\ub2e4.",
    "Inspect a generated asset before accepting it.": "\uc0dd\uc131\ub41c \uc5d0\uc14b\uc744 \uc2b9\uc778\ud558\uae30 \uc804 \ud655\uc778\ud569\ub2c8\ub2e4.",
    "Review skeleton and skinning results when a rig is available.": "\ub9ac\uae45 \uacb0\uacfc\uc758 \uc2a4\ucf08\ub808\ud1a4\uacfc \uc2a4\ud0a4\ub2dd\uc744 \uac80\ud1a0\ud569\ub2c8\ub2e4.",
    "Edit and preview a validated rig in a later phase.": "\uac80\uc99d\ub41c \ub9ac\uadf8\uc758 \ud3ec\uc988\uc640 \uc560\ub2c8\uba54\uc774\uc158\uc744 \ud3b8\uc9d1\ud569\ub2c8\ub2e4.",
    "Local readiness and accessibility preferences.": "\ub85c\uceec \uc900\ube44 \uc0c1\ud0dc\uc640 \uc811\uadfc\uc131 \uc124\uc815\uc785\ub2c8\ub2e4.",
}


class LanguageManager(QObject):
    """Persist a local language choice and update common Qt text at runtime."""

    changed = Signal(str)

    def __init__(self, settings_path: Path) -> None:
        super().__init__()
        self._path = settings_path
        self.language = self._load()

    def translate(self, source: str) -> str:
        return _KO.get(source, source) if self.language == "ko" else source

    def set_language(self, language: str) -> None:
        if language not in {"en", "ko"} or language == self.language:
            return
        self.language = language
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps({"language": language}), encoding="utf-8")
        self.changed.emit(language)

    def apply(self, root: QWidget) -> None:
        for widget in [root, *root.findChildren(QWidget)]:
            if isinstance(widget, (QLabel, QAbstractButton)):
                source = widget.property("i18nSource") or widget.text()
                widget.setProperty("i18nSource", source)
                widget.setText(self.translate(str(source)))
            elif isinstance(widget, QLineEdit):
                source = widget.property("i18nPlaceholder") or widget.placeholderText()
                widget.setProperty("i18nPlaceholder", source)
                widget.setPlaceholderText(self.translate(str(source)))
            elif isinstance(widget, QComboBox) and widget.objectName() != "languageSelector":
                for index in range(widget.count()):
                    source = widget.itemData(index, 0x0100) or widget.itemText(index)
                    widget.setItemData(index, source, 0x0100)
                    widget.setItemText(index, self.translate(str(source)))

    def _load(self) -> str:
        try:
            language = json.loads(self._path.read_text(encoding="utf-8")).get("language")
            return language if language in {"en", "ko"} else "en"
        except (OSError, ValueError, json.JSONDecodeError):
            return "en"
