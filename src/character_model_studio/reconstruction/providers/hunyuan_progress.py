"""Progress observation for the locally installed Hunyuan3D Shape pipeline."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Iterator
from contextlib import contextmanager
from typing import TypeVar, cast

ProgressCallback = Callable[[str, int, int], None]
_Item = TypeVar("_Item")


class _ObservedIterable(Iterable[_Item]):
    """Yield an upstream progress iterable while reporting completed work units."""

    def __init__(self, iterable: Iterable[_Item], stage: str, callback: ProgressCallback) -> None:
        self._iterable = iterable
        self._stage = stage
        self._callback = callback

    def __iter__(self) -> Iterator[_Item]:
        total = len(self._iterable)  # type: ignore[arg-type]
        for completed, item in enumerate(self._iterable, start=1):
            yield item
            self._callback(self._stage, completed, total)


def _stage_for_description(description: object) -> str | None:
    text = str(description)
    if text.startswith("Diffusion Sampling"):
        return "diffusion"
    if "Volume Decoding" in text:
        return "volume"
    return None


@contextmanager
def observe_hunyuan_shape_progress(callback: ProgressCallback) -> Iterator[None]:
    """Bridge Hunyuan's real tqdm loops to the application task progress stream.

    Hunyuan3D 2.0 exposes no public UI callback for its volume decoder. Its
    Shape pipeline does expose actual iteration totals through local tqdm loops,
    so this short-lived in-process adapter observes those loops without changing
    the installed upstream source tree.
    """
    from hy3dgen.shapegen import pipelines  # type: ignore[import-not-found]
    from hy3dgen.shapegen.models.autoencoders import (  # type: ignore[import-not-found]
        volume_decoders,
    )

    original_pipeline_tqdm = pipelines.tqdm
    original_decoder_tqdm = volume_decoders.tqdm

    def observing_tqdm(
        iterable: Iterable[_Item], *args: object, **kwargs: object
    ) -> Iterable[_Item]:
        stage = _stage_for_description(kwargs.get("desc"))
        if stage is None:
            return cast(Iterable[_Item], original_pipeline_tqdm(iterable, *args, **kwargs))
        return _ObservedIterable(iterable, stage, callback)

    pipelines.tqdm = observing_tqdm
    volume_decoders.tqdm = observing_tqdm
    try:
        yield
    finally:
        pipelines.tqdm = original_pipeline_tqdm
        volume_decoders.tqdm = original_decoder_tqdm
