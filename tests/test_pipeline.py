"""Camera pipeline tests (Sprint 11).

Tests the deterministic TestCameraSource, the CameraWorker orchestration
(detection -> tracking -> zone -> dwell -> camera-scoped events), and worker
failure isolation without requiring RTSP, ONVIF, or a GPU.
"""

from __future__ import annotations

import threading

import numpy as np

from ai.analytics import DwellTimeAnalyzer, Zone, ZoneEngine
from ai.detection.types import BBox, Detection
from ai.tracking.types import TrackResult, TrackState
from backend.pipeline import (
    CameraRuntimeStatus,
    CameraWorker,
    PipelineManager,
    TestCameraSource,
)
from backend.realtime import Event, EventType

HALF_FRAME_ZONE = Zone(
    zone_id="left",
    name="Left half",
    polygon=((0, 0), (50, 0), (50, 50), (0, 50)),
)


def _frame() -> np.ndarray:
    return np.zeros((100, 100, 3), dtype=np.uint8)


def _detection(x1: float, y1: float, x2: float, y2: float) -> Detection:
    return Detection(class_id=0, class_name="person", confidence=0.9, bbox=BBox(x1, y1, x2, y2))


class ScriptedDetector:
    def __init__(self, detections_per_call: list[list[Detection]]) -> None:
        self._detections = detections_per_call
        self._index = 0

    def detect(self, frame: np.ndarray) -> list[Detection]:
        if self._index >= len(self._detections):
            return []
        result = self._detections[self._index]
        self._index += 1
        return result


class ScriptedTracker:
    def __init__(self, results_per_call: list[list[TrackResult]]) -> None:
        self._results = results_per_call
        self._index = 0

    def update(self, detections: list[Detection]) -> list[TrackResult]:
        if self._index >= len(self._results):
            return []
        result = self._results[self._index]
        self._index += 1
        return result


class FailingSource(TestCameraSource):
    def __init__(self) -> None:
        super().__init__([_frame()])

    def read(self) -> np.ndarray | None:
        raise RuntimeError("camera failure")


def _make_worker(camera_id: str, publish) -> CameraWorker:
    detector = ScriptedDetector([[_detection(10, 10, 30, 30)], [_detection(60, 60, 80, 80)]])
    tracker = ScriptedTracker(
        [
            [TrackResult(0, 0, "person", 0.9, BBox(10, 10, 30, 30), TrackState.NEW)],
            [TrackResult(0, 0, "person", 0.9, BBox(60, 60, 80, 80), TrackState.ACTIVE)],
        ]
    )
    source = TestCameraSource([_frame(), _frame()])
    return CameraWorker(
        camera_id=camera_id,
        source=source,
        detector=detector,
        tracker=tracker,
        zone_engine=ZoneEngine([HALF_FRAME_ZONE]),
        dwell=DwellTimeAnalyzer(),
        publish=publish,
    )


# --- Test camera source ---


def test_test_camera_source_yields_then_exhausts() -> None:
    source = TestCameraSource([_frame(), _frame()])
    assert source.open() is True
    assert source.read() is not None
    assert source.read() is not None
    assert source.read() is None
    source.close()
    assert source.status == "closed"


# --- Camera worker ---


def test_worker_step_publishes_camera_scoped_events() -> None:
    published: list[Event] = []
    worker = _make_worker("cam-1", published.append)

    while not worker.exhausted:
        worker.step()

    types = [event.type.value for event in published]
    assert types == [
        "track_created",
        "zone_enter",
        "dwell_started",
        "track_updated",
        "zone_exit",
        "dwell_completed",
    ]
    assert all(event.camera_id == "cam-1" for event in published)

    completed = [e for e in published if e.type is EventType.DWELL_COMPLETED]
    assert completed[0].data["duration"] >= 0


def test_worker_run_isolates_failure() -> None:
    published: list[Event] = []
    worker = CameraWorker(
        camera_id="cam-broken",
        source=FailingSource(),
        detector=ScriptedDetector([[_detection(10, 10, 30, 30)]]),
        tracker=ScriptedTracker(
            [[TrackResult(0, 0, "person", 0.9, BBox(10, 10, 30, 30), TrackState.NEW)]]
        ),
        zone_engine=ZoneEngine([HALF_FRAME_ZONE]),
        dwell=DwellTimeAnalyzer(),
        publish=published.append,
    )

    worker.run(threading.Event(), poll_interval=0.0)

    assert worker.status is CameraRuntimeStatus.ERROR
    assert published == []


def test_worker_run_processes_finite_source() -> None:
    published: list[Event] = []
    worker = _make_worker("cam-1", published.append)
    worker.run(threading.Event(), poll_interval=0.0)
    assert worker.status is CameraRuntimeStatus.STOPPED
    assert any(e.type is EventType.ZONE_ENTER for e in published)


# --- Pipeline manager ---


def test_pipeline_manager_status_unknown_when_not_started() -> None:
    manager = PipelineManager()
    assert manager.status("cam-x") is CameraRuntimeStatus.UNKNOWN


def test_pipeline_manager_emits_lifecycle_events() -> None:
    published: list[Event] = []
    manager = PipelineManager(publish=published.append)
    worker = _make_worker("cam-1", lambda _e: None)

    manager.start("cam-1", worker, poll_interval=0.0)
    thread = manager._threads["cam-1"]  # noqa: SLF001
    thread.join(timeout=5)

    lifecycle = [e.type.value for e in published]
    assert "camera_connected" in lifecycle
    assert "camera_disconnected" in lifecycle
    assert all(e.camera_id == "cam-1" for e in published)


def test_pipeline_manager_stop_all_is_safe() -> None:
    manager = PipelineManager()
    manager.stop_all()
    assert manager.statuses() == {}
