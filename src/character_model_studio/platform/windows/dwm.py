"""Optional Windows DWM backdrop enhancement with a safe visual fallback."""

from __future__ import annotations

import ctypes
import sys
from ctypes import wintypes

DWMWA_SYSTEMBACKDROP_TYPE = 38
DWMSBT_MAINWINDOW = 2


def enable_system_backdrop(window_id: int) -> bool:
    """Request a Windows 11 system backdrop when the operating system supports it."""
    if sys.platform != "win32":
        return False

    backdrop_type = ctypes.c_int(DWMSBT_MAINWINDOW)
    result: int = ctypes.windll.dwmapi.DwmSetWindowAttribute(
        wintypes.HWND(window_id),
        DWMWA_SYSTEMBACKDROP_TYPE,
        ctypes.byref(backdrop_type),
        ctypes.sizeof(backdrop_type),
    )
    return result == 0
