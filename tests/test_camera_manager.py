"""Tests for multi-camera management."""

import numpy as np
import pytest

from ai.camera.config import CameraConfig
from ai.camera.exceptions import CameraError
from ai.camera.manager import CameraManager
from ai.camera.stream import StreamStatus


class FakeCapture:
    def __init__(self, url: str):
        self.url = url
        self._opened = True
        self.released = False

    def isOpened(self) -> bool:
        return self._opened

    def read(self):
        return (True, np.zeros((4, 4, 3), dtype=np.uint8))

    def release(self) -> None:
        self._opened = False
        self.released = True


def make_config(camera_id: str, *, enabled: bool = True) -> CameraConfig:
    return CameraConfig(
        id=camera_id,
        name=camera_id,
        rtsp_url=f"rtsp://localhost/{camera_id}",
        enabled=enabled,
    )


def make_manager() -> CameraManager:
    return CameraManager(capture_factory=lambda url: FakeCapture(url))


def test_manager_registers_and_lists() -> None:
    manager = make_manager()
    manager.add(make_config("cam-1"))
    manager.add(make_config("cam-2"))
    assert set(manager.list_ids()) == {"cam-1", "cam-2"}


def test_manager_duplicate_raises() -> None:
    manager = make_manager()
    manager.add(make_config("cam-1"))
    with pytest.raises(CameraError):
        manager.add(make_config("cam-1"))


def test_manager_start_only_enabled() -> None:
    manager = make_manager()
    manager.add(make_config("cam-1"))
    manager.add(make_config("cam-2", enabled=False))

    results = manager.start()
    assert results == {"cam-1": True}
    assert manager.status()["cam-1"] is StreamStatus.CONNECTED
    assert manager.status()["cam-2"] is StreamStatus.DISCONNECTED


def test_manager_stop_releases_all() -> None:
    manager = make_manager()
    manager.add(make_config("cam-1"))
    manager.add(make_config("cam-2"))
    manager.start()
    manager.stop()
    assert manager.status()["cam-1"] is StreamStatus.CLOSED
    assert manager.status()["cam-2"] is StreamStatus.CLOSED


def test_manager_get_and_remove() -> None:
    manager = make_manager()
    manager.add(make_config("cam-1"))
    assert manager.get("cam-1").config.id == "cam-1"
    manager.remove("cam-1")
    assert manager.list_ids() == []


def test_manager_unknown_camera_raises() -> None:
    manager = make_manager()
    with pytest.raises(CameraError):
        manager.get("nope")
    with pytest.raises(CameraError):
        manager.remove("nope")
