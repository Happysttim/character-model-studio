"""Cooperative cancellation shared by local background work."""

from __future__ import annotations

from threading import Event


class CancellationToken:
    """Thread-safe cancellation signal without a server or task queue."""

    def __init__(self) -> None:
        self._event = Event()

    def cancel(self) -> None:
        self._event.set()

    @property
    def is_cancelled(self) -> bool:
        return self._event.is_set()
