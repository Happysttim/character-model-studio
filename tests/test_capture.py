"""Capture geometry and local worker lifecycle tests without a real desktop recording."""

from __future__ import annotations

from pathlib import Path

import av
import numpy as np
import pytest

from character_model_studio.capture.models import CaptureSettings, PhysicalRegion
from character_model_studio.capture.importer import import_video
from character_model_studio.capture.recorder import FrameSource, PyAvH264Encoder, VideoEncoder
from character_model_studio.capture.region import LogicalRect, MonitorGeometry, to_physical_region
from character_model_studio.capture.session import CaptureSession


class FixtureFrameSource:
    """Deterministic BGR source used to exercise the same worker contract as DXcam."""

    def __init__(self) -> None:
        self.started = False
        self.stopped = False
        self._frame: np.ndarray | None = None

    def start(self, region: PhysicalRegion, fps: int) -> None:
        self.started = True
        self._frame = np.full((region.height, region.width, 3), 128, dtype=np.uint8)

    def latest_frame(self) -> np.ndarray | None:
        return self._frame

    def stop(self) -> None:
        self.stopped = True


class FixtureEncoder:
    """Small file encoder fixture that proves the capture lifecycle independently of FFmpeg."""

    def __init__(self, path: Path, width: int, height: int, fps: int) -> None:
        self._path = path
        self._frames = 0

    def write(self, frame: np.ndarray) -> None:
        self._frames += 1

    def close(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_bytes(f"fixture-h264-frame-count={self._frames}".encode())


@pytest.mark.parametrize(
    ("scale", "expected"),
    [
        (1.0, PhysicalRegion(100, 50, 640, 480, "primary")),
        (1.25, PhysicalRegion(125, 62, 800, 600, "primary")),
        (1.5, PhysicalRegion(150, 75, 960, 720, "primary")),
        (2.0, PhysicalRegion(200, 100, 1280, 960, "primary")),
    ],
)
def test_region_conversion_is_dpi_correct(scale: float, expected: PhysicalRegion) -> None:
    monitor = MonitorGeometry("primary", 0, 0, 1920, 1080, scale)
    region = to_physical_region(LogicalRect(100, 50, 640, 480), monitor)

    assert region == expected


def test_region_conversion_rejects_cross_monitor_and_too_small_selection() -> None:
    monitor = MonitorGeometry("primary", 0, 0, 1000, 700, 1.0)
    try:
        to_physical_region(LogicalRect(900, 100, 200, 200), monitor)
    except ValueError as error:
        assert "one monitor" in str(error)
    else:
        raise AssertionError("Cross-monitor selection must be rejected")

    try:
        to_physical_region(LogicalRect(10, 10, 100, 100), monitor)
    except ValueError as error:
        assert "at least" in str(error)
    else:
        raise AssertionError("Small selection must be rejected")


def test_region_conversion_trims_odd_dimensions_for_h264_yuv420p() -> None:
    monitor = MonitorGeometry("primary", 0, 0, 1920, 1080, 1.0)

    region = to_physical_region(LogicalRect(100, 100, 641, 481), monitor)

    assert (region.width, region.height) == (640, 480)


def test_capture_session_stops_idempotently_and_releases_resources(qtbot, tmp_path) -> None:
    sources: list[FixtureFrameSource] = []

    def create_source() -> FrameSource:
        source = FixtureFrameSource()
        sources.append(source)
        return source

    def create_encoder(path: Path, width: int, height: int, fps: int) -> VideoEncoder:
        return FixtureEncoder(path, width, height, fps)

    session = CaptureSession(create_source, create_encoder)
    region = PhysicalRegion(0, 0, 320, 240, "primary")
    video_path = tmp_path / "capture.mp4"
    thumbnail_path = tmp_path / "thumbnail.jpg"

    with qtbot.waitSignal(session.completed, timeout=3000) as completed:
        session.start(region, video_path, thumbnail_path, CaptureSettings(fps=30))
        qtbot.waitUntil(lambda: bool(sources) and sources[0].started)
        session.stop()
        session.stop()

    result = completed.args[0]
    assert result.video_path == video_path
    assert video_path.is_file()
    assert thumbnail_path.is_file()
    assert (tmp_path / "capture.json").is_file()
    assert sources[0].started and sources[0].stopped


def test_pyav_encoder_writes_reopenable_h264_mp4(tmp_path) -> None:
    output = tmp_path / "capture.mp4"
    encoder = PyAvH264Encoder(output, 320, 240, 30)
    encoder.write(np.zeros((240, 320, 3), dtype=np.uint8))
    encoder.close()

    with av.open(str(output)) as container:
        stream = container.streams.video[0]
        assert stream.codec_context.name == "h264"
    assert stream.width == 320
    assert stream.height == 240


def test_pyav_encoder_rejects_odd_h264_dimensions(tmp_path) -> None:
    with pytest.raises(ValueError, match="even pixel dimensions"):
        PyAvH264Encoder(tmp_path / "odd.mp4", 641, 481, 30)


def test_imported_video_creates_managed_copy_and_thumbnail(tmp_path) -> None:
    source = tmp_path / "source.mp4"
    encoder = PyAvH264Encoder(source, 320, 240, 30)
    encoder.write(np.full((240, 320, 3), 128, dtype=np.uint8))
    encoder.close()

    result = import_video(
        source, tmp_path / "managed" / "capture.mp4", tmp_path / "managed" / "thumbnail.jpg"
    )

    assert result.video_path.is_file()
    assert result.thumbnail_path.is_file()
    assert result.width == 320
    assert result.height == 240
    assert result.frame_count >= 1
