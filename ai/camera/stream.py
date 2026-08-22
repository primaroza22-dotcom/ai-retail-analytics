"""RTSP/HTTP camera stream reader with automatic reconnect."""

from __future__ import annotations

import time
from collections.abc import Callable
from enum import Enum
from typing import Any

import numpy as np

from .config import CameraConfig

CaptureFactory = Callable[[str], Any]


def default_capture_factory(url: str) -> Any:
    """Create a real OpenCV video capture.

    ``opencv-python`` is imported lazily so the camera subsystem (and its
    tests) remain importable without the heavyweight video backend.
    """
    import cv2

    return cv2.VideoCapture(url)


class StreamStatus(Enum):
    """Connection state of a camera stream."""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    CLOSED = "closed"
    ERROR = "error"


class CameraStream:
    """Wraps a video capture and tracks connection state + reconnection."""

    def __init__(
        self,
        config: CameraConfig,
        capture_factory: CaptureFactory | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.config = config
        self._capture_factory = capture_factory or default_capture_factory
        self._sleep = sleep
        self._capture: Any = None
        self._status = StreamStatus.DISCONNECTED
        self._reconnect_attempts = 0

    @property
    def status(self) -> StreamStatus:
        return self._status

    @property
    def is_connected(self) -> bool:
        return self._status is StreamStatus.CONNECTED and bool(
            self._capture is not None and self._capture.isOpened()
        )

    @property
    def reconnect_attempts(self) -> int:
        return self._reconnect_attempts

    def open(self) -> bool:
        self._status = StreamStatus.CONNECTING
        capture = self._capture_factory(self.config.rtsp_url)
        if capture is not None and capture.isOpened():
            self._capture = capture
            self._status = StreamStatus.CONNECTED
            return True
        self._capture = None
        self._status = StreamStatus.DISCONNECTED
        return False

    def read(self) -> np.ndarray | None:
        if self._status is StreamStatus.CLOSED:
            return None
        if not self.is_connected and not self._reconnect():
            return None
        ret, frame = self._capture.read()
        if not ret or frame is None:
            self._status = StreamStatus.DISCONNECTED
            return None
        return frame

    def close(self) -> None:
        if self._capture is not None:
            self._capture.release()
        self._capture = None
        self._status = StreamStatus.CLOSED

    def _reconnect(self) -> bool:
        max_attempts = self.config.max_reconnect_attempts
        attempts = 0
        while max_attempts is None or attempts < max_attempts:
            attempts += 1
            self._reconnect_attempts += 1
            self._status = StreamStatus.RECONNECTING
            if self.open():
                return True
            if max_attempts is not None and attempts >= max_attempts:
                break
            self._sleep(self.config.reconnect_interval)
        self._status = StreamStatus.ERROR
        return False
