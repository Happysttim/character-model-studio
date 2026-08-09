"""Background DXcam capture and local H.264 MP4 encoding."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from threading import Event
from time import monotonic, sleep
from typing import Any, Protocol, cast

import av
import cv2
import numpy as np
from PySide6.QtCore import QObject, Signal, Slot

from character_model_studio.capture.models import CaptureResult, CaptureSettings, PhysicalRegion


class FrameSource(Protocol):
    """A capture backend that returns BGR frames from the selected physical region."""

    def start(self, region: PhysicalRegion, fps: int) -> None: ...

    def latest_frame(self) -> np.ndarray | None: ...

    def stop(self) -> None: ...


class VideoEncoder(Protocol):
    """Local video container writer used by the capture worker."""

    def write(self, frame: np.ndarray) -> None: ...

    def close(self) -> None: ...


class DxcamFrameSource:
    """Windows Desktop Duplication adapter; imported only when capture starts."""

    def __init__(self) -> None:
        self._camera: Any | None = None
        self._region: PhysicalRegion | None = None

    def start(self, region: PhysicalRegion, fps: int) -> None:
        import dxcam  # type: ignore[import-untyped]

        self._camera = dxcam.create(output_color="BGR")
        self._region = region
        self._camera.start(
            region=(region.left, region.top, region.right, region.bottom), target_fps=fps
        )

    def latest_frame(self) -> np.ndarray | None:
        if self._camera is None:
            raise RuntimeError("DXcam capture has not started")
        return cast(np.ndarray | None, self._camera.get_latest_frame())

    def stop(self) -> None:
        if self._camera is not None:
            self._camera.stop()
            self._camera = None
            self._region = None


class PyAvH264Encoder:
    """MP4/H.264 encoder that receives BGR NumPy frames locally."""

    def __init__(self, path: Path, width: int, height: int, fps: int) -> None:
        if width % 2 or height % 2:
            raise ValueError(
                "H.264 recording requires even pixel dimensions; "
                "select a region with even width and height"
            )
        path.parent.mkdir(parents=True, exist_ok=True)
        self._container = av.open(str(path), mode="w", format="mp4")
        self._stream = self._container.add_stream("libx264", rate=fps)
        self._stream.width = width
        self._stream.height = height
        self._stream.pix_fmt = "yuv420p"

    def write(self, frame: np.ndarray) -> None:
        video_frame = av.VideoFrame.from_ndarray(frame, format="bgr24")
        for packet in self._stream.encode(video_frame):
            self._container.mux(packet)

    def close(self) -> None:
        for packet in self._stream.encode():
            self._container.mux(packet)
        self._container.close()


class CaptureWorker(QObject):
    """Owns capture and encoding resources on a worker thread."""

    progress = Signal(int)
    completed = Signal(object)
    failed = Signal(str)

    def __init__(
        self,
        region: PhysicalRegion,
        video_path: Path,
        thumbnail_path: Path,
        settings: CaptureSettings,
        frame_source_factory: Callable[[], FrameSource] = DxcamFrameSource,
        encoder_factory: Callable[[Path, int, int, int], VideoEncoder] = PyAvH264Encoder,
    ) -> None:
        super().__init__()
        self._region = region
        self._video_path = video_path
        self._thumbnail_path = thumbnail_path
        self._settings = settings
        self._frame_source_factory = frame_source_factory
        self._encoder_factory = encoder_factory
        self._stop_requested = Event()

    def request_stop(self) -> None:
        """Request a safe, idempotent stop from the UI thread."""
        self._stop_requested.set()

    @Slot()
    def run(self) -> None:
        source = self._frame_source_factory()
        encoder: VideoEncoder | None = None
        frame_count = 0
        started_at = monotonic()
        last_frame: np.ndarray | None = None
        try:
            source.start(self._region, self._settings.fps)
            encoder = self._encoder_factory(
                self._video_path, self._region.width, self._region.height, self._settings.fps
            )
            next_frame_at = monotonic()
            while not self._stop_requested.is_set():
                frame = source.latest_frame()
                if frame is not None:
                    if frame.shape[:2] != (self._region.height, self._region.width):
                        raise RuntimeError("Capture frame dimensions changed during recording")
                    encoder.write(frame)
                    last_frame = frame
                    frame_count += 1
                self.progress.emit(round((monotonic() - started_at) * 1000))
                next_frame_at += 1 / self._settings.fps
                sleep(max(0.0, next_frame_at - monotonic()))
            if frame_count == 0 or last_frame is None:
                raise RuntimeError("No frames were captured; check the display and capture device")
            encoder.close()
            encoder = None
            self._thumbnail_path.parent.mkdir(parents=True, exist_ok=True)
            if not cv2.imwrite(str(self._thumbnail_path), last_frame):
                raise RuntimeError("Could not write capture thumbnail")
            duration_ms = round((monotonic() - started_at) * 1000)
            metadata_path = self._video_path.with_name("capture.json")
            metadata_path.write_text(
                json.dumps(
                    {
                        "durationMs": duration_ms,
                        "width": self._region.width,
                        "height": self._region.height,
                        "fps": self._settings.fps,
                        "codec": self._settings.codec,
                        "audio": False,
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            self.completed.emit(
                CaptureResult(
                    self._video_path,
                    self._thumbnail_path,
                    duration_ms,
                    self._region.width,
                    self._region.height,
                    self._settings.fps,
                    frame_count,
                )
            )
        except (av.FFmpegError, OSError, RuntimeError, ValueError) as error:
            self.failed.emit(str(error))
        finally:
            if encoder is not None:
                encoder.close()
            source.stop()
