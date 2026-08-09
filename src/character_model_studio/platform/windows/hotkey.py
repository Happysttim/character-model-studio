"""Isolated Win32 global-hotkey registration for the capture workflow."""

from __future__ import annotations

import ctypes
import sys
from collections.abc import Callable
from ctypes import wintypes

from PySide6.QtCore import QAbstractNativeEventFilter, QByteArray

MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
VK_S = 0x53
WM_HOTKEY = 0x0312


class _Message(ctypes.Structure):
    _fields_ = [
        ("hwnd", wintypes.HWND),
        ("message", wintypes.UINT),
        ("wParam", wintypes.WPARAM),
        ("lParam", wintypes.LPARAM),
        ("time", wintypes.DWORD),
        ("pt_x", wintypes.LONG),
        ("pt_y", wintypes.LONG),
    ]


class WindowsCaptureHotkey(QAbstractNativeEventFilter):
    """Register and release the MVP Ctrl+Alt+S global hotkey."""

    def __init__(self, callback: Callable[[], None], hotkey_id: int = 0x4353) -> None:
        super().__init__()
        self._callback = callback
        self._hotkey_id = hotkey_id
        self._registered = False

    @property
    def is_registered(self) -> bool:
        """Return whether registration has succeeded in this process."""
        return self._registered

    def register(self) -> bool:
        """Register Ctrl+Alt+S, returning False when Windows reports a conflict."""
        if self._registered:
            return True
        if sys.platform != "win32":
            return False
        result = ctypes.windll.user32.RegisterHotKey(
            wintypes.HWND(), self._hotkey_id, MOD_CONTROL | MOD_ALT, VK_S
        )
        self._registered = result != 0
        return self._registered

    def release(self) -> None:
        """Release the hotkey exactly once during shutdown."""
        if self._registered and sys.platform == "win32":
            ctypes.windll.user32.UnregisterHotKey(wintypes.HWND(), self._hotkey_id)
        self._registered = False

    def nativeEventFilter(  # noqa: N802
        self, event_type: QByteArray | bytes | bytearray | memoryview[int], message: int
    ) -> tuple[bool, int]:
        """Forward the process-level WM_HOTKEY message to the Qt capture controller."""
        if event_type == b"windows_generic_MSG":
            native_message = _Message.from_address(int(message))
            if native_message.message == WM_HOTKEY and native_message.wParam == self._hotkey_id:
                self._callback()
                return True, 0
        return False, 0
