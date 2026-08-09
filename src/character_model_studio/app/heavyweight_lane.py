"""Single-owner orchestration for CUDA-heavy provider lifecycles."""

from __future__ import annotations

from collections.abc import Callable
from threading import Lock
from typing import TypeVar

import torch

Result = TypeVar("Result")


class HeavyweightTaskLane:
    """Serialize provider load/work/unload so heavy models do not overlap in VRAM."""

    def __init__(self) -> None:
        self._lock = Lock()

    def run(
        self, load: Callable[[], None], work: Callable[[], Result], unload: Callable[[], None]
    ) -> Result:
        """Run one provider lifecycle, always attempting cleanup after work."""
        with self._lock:
            loaded = False
            try:
                load()
                loaded = True
                return work()
            finally:
                if loaded:
                    unload()
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
