"""Optional integration test wiring CameraStream -> YOLODetector.

No physical CCTV is required: a fake capture yields a real image frame.
"""

import pytest

from ai.camera.config import CameraConfig
from ai.camera.stream import CameraStream


class FakeCapture:
    def __init__(self, frame):
        self._opened = True
        self._frame = frame

    def isOpened(self) -> bool:
        return self._opened

    def read(self):
        return (True, self._frame)

    def release(self) -> None:
        self._opened = False


def _load_bus_image():
    import cv2

    from ultralytics.utils import ASSETS

    return cv2.imread(str(ASSETS / "bus.jpg"))


@pytest.mark.integration
def test_camera_stream_to_detector(detector) -> None:
    frame = _load_bus_image()
    capture = FakeCapture(frame)
    stream = CameraStream(
        CameraConfig(id="cam", name="cam", rtsp_url="rtsp://fake/stream1"),
        capture_factory=lambda url: capture,
    )

    stream.open()
    detected_frame = stream.read()
    assert detected_frame is not None

    detections = detector.detect(detected_frame)
    assert any(d.class_name == "person" for d in detections)

    stream.close()
