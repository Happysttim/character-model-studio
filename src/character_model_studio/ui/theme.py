"""Centralized warm glass design tokens and Qt stylesheet generation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ThemeTokens:
    """The small, deliberate palette shared by every Qt Widgets surface."""

    canvas_warm: str = "#F5E6D7"
    canvas_warm_alt: str = "#E7C8AF"
    glass_base: str = "rgba(255, 250, 244, 0.62)"
    glass_raised: str = "rgba(255, 252, 248, 0.70)"
    glass_strong: str = "rgba(255, 248, 240, 0.80)"
    border_soft: str = "rgba(143, 79, 50, 0.22)"
    border_focus: str = "rgba(255, 181, 122, 0.65)"
    text_primary: str = "#3E241B"
    text_secondary: str = "#633C2E"
    text_muted: str = "#876657"
    amber: str = "#F2A65A"
    apricot: str = "#FFBE88"
    coral: str = "#E97B67"
    terracotta: str = "#C96A4B"
    cream: str = "#FFE4CB"
    success: str = "#9CCB9A"
    warning: str = "#E6B86C"
    danger: str = "#E57464"
    info: str = "#A9BED1"


TOKENS = ThemeTokens()


def application_stylesheet(tokens: ThemeTokens = TOKENS) -> str:
    """Build the native Qt stylesheet from the centralized design tokens."""
    return f"""
        QWidget {{
            color: {tokens.text_primary};
            font-family: "Segoe UI", "Malgun Gothic", sans-serif;
            font-size: 14px;
        }}
        QMainWindow#mainWindow {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #FCE5CF, stop:0.38 #F8D5BF, stop:0.7 #EFC9B6, stop:1 #DCC4B5);
        }}
        QFrame#windowTitleBar {{ background: rgba(255, 249, 241, 0.80); min-height: 38px; }}
        QPushButton#windowControl {{
            background: transparent; border: 0; color: {tokens.text_primary};
            min-width: 34px; min-height: 30px;
        }}
        QPushButton#windowControl:hover {{ background: rgba(201, 106, 75, 0.18); }}
        QFrame#navigationPane {{
            background-color: {tokens.canvas_warm_alt};
            border-right: 1px solid {tokens.border_soft};
        }}
        QFrame#workspaceSurface {{
            background-color: {tokens.glass_base};
            border: 0;
            border-radius: 0;
        }}
        QFrame[glassLevel="secondary"] {{
            background-color: {tokens.glass_raised};
            border: 1px solid {tokens.border_soft};
            border-radius: 14px;
        }}
        QFrame[glassLevel="floating"] {{
            background-color: {tokens.glass_strong};
            border: 1px solid {tokens.border_soft};
            border-radius: 10px;
        }}
        QLabel#brandName {{
            color: {tokens.cream};
            font-size: 18px;
            font-weight: 700;
        }}
        QLabel#brandCaption, QLabel#pageSubtitle {{
            color: {tokens.text_muted};
        }}
        QLabel#pageTitle {{
            color: {tokens.text_primary};
            font-size: 24px;
            font-weight: 650;
        }}
        QPushButton[navRole="item"] {{
            background: transparent;
            border: 1px solid transparent;
            border-radius: 10px;
            color: {tokens.text_secondary};
            min-height: 38px;
            padding: 0 12px;
            text-align: left;
        }}
        QPushButton[navRole="item"]:hover {{
            background-color: {tokens.glass_raised};
            color: {tokens.text_primary};
        }}
        QPushButton[navRole="item"]:checked {{
            background-color: rgba(242, 166, 90, 0.18);
            border-color: rgba(242, 166, 90, 0.55);
            color: {tokens.cream};
            font-weight: 600;
        }}
        QPushButton[navRole="item"]:focus, QPushButton:focus, QLineEdit:focus,
        QCheckBox:focus {{
            border: 1px solid {tokens.border_focus};
            outline: none;
        }}
        QPushButton[buttonKind="primary"] {{
            background-color: {tokens.amber};
            border: 1px solid {tokens.apricot};
            border-radius: 10px;
            color: #2A1710;
            font-weight: 700;
            min-height: 34px;
            padding: 0 14px;
        }}
        QPushButton[buttonKind="primary"]:hover {{ background-color: {tokens.apricot}; }}
        QPushButton[buttonKind="secondary"] {{
            background-color: {tokens.glass_raised};
            border: 1px solid {tokens.border_soft};
            border-radius: 10px;
            color: {tokens.text_primary};
            min-height: 34px;
            padding: 0 14px;
        }}
        QPushButton:disabled {{
            background-color: rgba(255, 244, 235, 0.05);
            border-color: rgba(255, 232, 218, 0.08);
            color: {tokens.text_muted};
        }}
        QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QListWidget {{
            background-color: rgba(255, 250, 244, 0.94);
            border: 1px solid {tokens.border_soft};
            border-radius: 6px;
            color: #2A1710;
            min-height: 30px;
            padding: 0 9px;
            selection-background-color: {tokens.terracotta};
        }}
        QComboBox QAbstractItemView, QListWidget::item {{
            background-color: #FFF8F0; color: #2A1710;
            selection-background-color: {tokens.apricot}; selection-color: #2A1710;
        }}
        QListWidget::item {{ padding: 8px; border-bottom: 1px solid {tokens.border_soft}; }}
        QPlainTextEdit#processingLog {{
            background-color: rgba(255, 250, 244, 0.82);
            border: 1px solid {tokens.border_soft};
            border-radius: 10px;
            color: #2A1710;
            font-family: "Noto Sans KR", "Noto Sans", "Segoe UI", "Malgun Gothic", sans-serif;
            font-size: 13px;
            padding: 10px;
            selection-background-color: {tokens.apricot};
        }}
        QProgressBar {{
            background-color: rgba(255, 250, 244, 0.70);
            border: 1px solid {tokens.border_soft};
            border-radius: 6px;
            color: #2A1710;
            min-height: 12px;
            text-align: center;
        }}
        QProgressBar::chunk {{
            background-color: {tokens.amber};
            border-radius: 5px;
        }}
        QLabel#capturePoster {{
            background-color: rgba(42, 33, 30, 0.18);
            border: 1px solid {tokens.border_soft};
        }}
        QCheckBox {{ color: {tokens.text_secondary}; spacing: 8px; }}
        QCheckBox::indicator {{
            width: 16px; height: 16px; border-radius: 4px;
            border: 1px solid {tokens.border_soft}; background: {tokens.canvas_warm_alt};
        }}
        QCheckBox::indicator:checked {{
            background: {tokens.amber}; border-color: {tokens.apricot};
        }}
        QLabel[statusTone="ready"] {{ color: {tokens.success}; }}
        QLabel[statusTone="warning"] {{ color: {tokens.warning}; }}
        QLabel[statusTone="info"] {{ color: {tokens.info}; }}
        QDialog {{ background-color: {tokens.canvas_warm_alt}; }}
    """
