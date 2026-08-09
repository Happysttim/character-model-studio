"""Centralized warm glass design tokens and Qt stylesheet generation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ThemeTokens:
    """The small, deliberate palette shared by every Qt Widgets surface."""

    canvas_warm: str = "#201B19"
    canvas_warm_alt: str = "#2A211E"
    glass_base: str = "rgba(255, 244, 235, 0.08)"
    glass_raised: str = "rgba(255, 248, 241, 0.12)"
    glass_strong: str = "rgba(255, 248, 241, 0.17)"
    border_soft: str = "rgba(255, 232, 218, 0.16)"
    border_focus: str = "rgba(255, 181, 122, 0.65)"
    text_primary: str = "#FFF7F1"
    text_secondary: str = "#D9C9BF"
    text_muted: str = "#A99589"
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
            background-color: {tokens.canvas_warm};
        }}
        QFrame#navigationPane {{
            background-color: {tokens.canvas_warm_alt};
            border-right: 1px solid {tokens.border_soft};
        }}
        QFrame#workspaceSurface {{
            background-color: {tokens.glass_base};
            border: 1px solid {tokens.border_soft};
            border-radius: 18px;
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
        QLineEdit {{
            background-color: rgba(16, 12, 11, 0.42);
            border: 1px solid {tokens.border_soft};
            border-radius: 6px;
            color: {tokens.text_primary};
            min-height: 30px;
            padding: 0 9px;
            selection-background-color: {tokens.terracotta};
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
