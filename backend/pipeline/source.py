"""Camera source abstraction.

A camera source is the input for one pipeline. Concrete implementations
(RTSP/ONVIF) are kept separate from the detection/tracking/zone/dwell logic so
that tests can use a deterministic in-memory source without a physical camera.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum

import numpy as np


class CameraRuntimeStatus(str, Enum):
    UNKNOWN = "unknown"
    STARTING = "starting"
    CONNECTED = "connected"
    RUNNING = "running"
    RECONNECTING = "reconnecting"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    STOPPED = "stopped"


class CameraSource(ABC):
    """Interface for a single camera's frame source."""

    @abstractmethod
    def open(self) -> bool:
        """Open the source; return True on success."""

    @abstractmethod
    def read(self) -> np.ndarray | None:
        """Return the next frame, or None when exhausted/unavailable."""

    @abstractmethod
    def close(self) -> None:
        """Release the source."""

    @property
    @abstractmethod
    def status(self) -> str:
        """Return a short connection status string."""


class TestCameraSource(CameraSource):
    """Deterministic in-memory source that yields pre-scripted frames.

    Used by automated tests to simulate a camera without RTSP/ONVIF/GPU.
    """

    __test__ = False  # not a pytest test class

    def __init__(self, frames: list[np.ndarray]) -> None:
        self._frames = list(frames)
        self._index = 0
        self._opened = False
        self._closed = False

    def open(self) -> bool:
        self._opened = True
        return True

    def read(self) -> np.ndarray | None:
        if self._closed or not self._opened or self._index >= len(self._frames):
            return None
        frame = self._frames[self._index]
        self._index += 1
        return frame

    def close(self) -> None:
        self._closed = True

    @property
    def status(self) -> str:
        if self._closed:
            return "closed"
        if not self._opened:
            return "disconnected"
        return "connected"
