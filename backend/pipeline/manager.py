"""Pipeline manager: runs one isolated worker thread per camera.

A single camera worker's failure never terminates the manager or the FastAPI
application; each worker runs in its own thread and reports its own status.
Camera lifecycle events (connected/disconnected/error) are published to the
real-time event bus when available.
"""

from __future__ import annotations

import threading
import time

from ..realtime import Event, EventType
from .source import CameraRuntimeStatus
from .worker import CameraWorker


class PipelineManager:
    """Owns and controls camera workers, keyed by camera id."""

    def __init__(self, publish=None) -> None:
        self._publish = publish
        self._workers: dict[str, CameraWorker] = {}
        self._threads: dict[str, threading.Thread] = {}
        self._stop_events: dict[str, threading.Event] = {}

    def _emit(self, event_type: EventType, camera_id: str) -> None:
        if self._publish is not None:
            self._publish(Event(event_type, time.time(), {}, camera_id=camera_id))

    def start(self, camera_id: str, worker: CameraWorker, poll_interval: float = 0.0) -> None:
        if camera_id in self._threads:
            return
        stop_event = threading.Event()
        self._workers[camera_id] = worker
        self._stop_events[camera_id] = stop_event
        self._emit(EventType.CAMERA_CONNECTED, camera_id)

        def _run() -> None:
            worker.run(stop_event, poll_interval)
            if worker.status is CameraRuntimeStatus.ERROR:
                self._emit(EventType.CAMERA_ERROR, camera_id)
            self._emit(EventType.CAMERA_DISCONNECTED, camera_id)

        thread = threading.Thread(
            target=_run,
            name=f"camera-worker-{camera_id}",
            daemon=True,
        )
        self._threads[camera_id] = thread
        thread.start()

    def stop(self, camera_id: str) -> None:
        stop_event = self._stop_events.pop(camera_id, None)
        if stop_event is not None:
            stop_event.set()
        self._threads.pop(camera_id, None)

    def stop_all(self) -> None:
        for camera_id in list(self._threads):
            self.stop(camera_id)

    def status(self, camera_id: str) -> CameraRuntimeStatus:
        worker = self._workers.get(camera_id)
        if worker is None:
            return CameraRuntimeStatus.UNKNOWN
        return worker.status

    def statuses(self) -> dict[str, str]:
        return {camera_id: worker.status.value for camera_id, worker in self._workers.items()}
