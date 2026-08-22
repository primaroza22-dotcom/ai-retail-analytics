"""Tests for the RTSP camera stream using a fake capture (no physical camera)."""

import numpy as np
import pytest

from ai.camera.config import CameraConfig
from ai.camera.stream import CameraStream, StreamStatus


class FakeCapture:
    """Minimal stand-in for cv2.VideoCapture."""

    def __init__(self, url: str, *, open_success: bool = True, read_success: bool = True):
        self.url = url
        self._opened = open_success
        self._read_success = read_success
        self.released = False
        self.read_calls = 0

    def isOpened(self) -> bool:
        return self._opened

    def read(self):
        self.read_calls += 1
        if not self._opened or not self._read_success:
            return (False, None)
        return (True, np.zeros((16, 16, 3), dtype=np.uint8))

    def release(self) -> None:
        self._opened = False
        self.released = True


def make_config(**overrides) -> CameraConfig:
    data = {"id": "cam-1", "name": "Entrance", "rtsp_url": "rtsp://localhost/stream1"}
    data.update(overrides)
    return CameraConfig(**data)


def test_open_success() -> None:
    stream = CameraStream(make_config(), capture_factory=lambda url: FakeCapture(url))
    assert stream.open() is True
    assert stream.status is StreamStatus.CONNECTED
    assert stream.is_connected is True


def test_open_failure() -> None:
    stream = CameraStream(
        make_config(), capture_factory=lambda url: FakeCapture(url, open_success=False)
    )
    assert stream.open() is False
    assert stream.status is StreamStatus.DISCONNECTED
    assert stream.is_connected is False


def test_read_returns_frame() -> None:
    stream = CameraStream(make_config(), capture_factory=lambda url: FakeCapture(url))
    stream.open()
    frame = stream.read()
    assert frame is not None
    assert frame.shape == (16, 16, 3)


def test_read_failure_drops_connection() -> None:
    stream = CameraStream(
        make_config(), capture_factory=lambda url: FakeCapture(url, read_success=False)
    )
    stream.open()
    assert stream.read() is None
    assert stream.is_connected is False
    assert stream.status is StreamStatus.DISCONNECTED


def test_reconnect_after_disconnect() -> None:
    calls = {"n": 0}

    def factory(url: str) -> FakeCapture:
        calls["n"] += 1
        if calls["n"] == 1:
            return FakeCapture(url, open_success=False)
        return FakeCapture(url)

    cfg = make_config(max_reconnect_attempts=3, reconnect_interval=0.0)
    stream = CameraStream(cfg, capture_factory=factory, sleep=lambda s: None)

    assert stream.open() is False
    frame = stream.read()
    assert frame is not None
    assert stream.status is StreamStatus.CONNECTED
    assert stream.reconnect_attempts == 1


def test_reconnect_gives_up_after_max_attempts() -> None:
    cfg = make_config(max_reconnect_attempts=2, reconnect_interval=0.0)
    stream = CameraStream(
        cfg,
        capture_factory=lambda url: FakeCapture(url, open_success=False),
        sleep=lambda s: None,
    )
    assert stream.read() is None
    assert stream.status is StreamStatus.ERROR
    assert stream.reconnect_attempts == 2


def test_close_releases_capture() -> None:
    capture = FakeCapture("url")
    stream = CameraStream(make_config(), capture_factory=lambda url: capture)
    stream.open()
    stream.close()
    assert capture.released is True
    assert stream.status is StreamStatus.CLOSED


def test_read_after_close_returns_none() -> None:
    stream = CameraStream(make_config(), capture_factory=lambda url: FakeCapture(url))
    stream.open()
    stream.close()
    assert stream.read() is None
