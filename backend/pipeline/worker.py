"""Camera worker: orchestrates one camera's detection/tracking/zone/dwell pipeline.

The worker is isolated per camera and publishes camera-scoped events. It depends
on injectable source, detector, tracker, zone engine, and dwell analyzer so the
real (YOLO/ByteTrack) implementations can be swapped for deterministic test
doubles.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import Any

from ai.analytics import DwellTimeAnalyzer, ZoneEngine, ZoneEventType
from ai.tracking.types import TrackState

from ..realtime import Event, EventType
from .source import CameraRuntimeStatus, CameraSource

logger = logging.getLogger(__name__)

EventPublisher = Callable[[Event], None]


class CameraWorker:
    """Runs the full pipeline for a single camera and emits camera-scoped events."""

    def __init__(
        self,
        camera_id: str,
        source: CameraSource,
        detector: Any,
        tracker: Any,
        zone_engine: ZoneEngine,
        dwell: DwellTimeAnalyzer,
        publish: EventPublisher,
    ) -> None:
        self._camera_id = camera_id
        self._source = source
        self._detector = detector
        self._tracker = tracker
        self._zone_engine = zone_engine
        self._dwell = dwell
        self._publish = publish
        self._status = CameraRuntimeStatus.STOPPED
        self._exhausted = False
        self._opened = False

    @property
    def camera_id(self) -> str:
        return self._camera_id

    @property
    def status(self) -> CameraRuntimeStatus:
        return self._status

    @property
    def exhausted(self) -> bool:
        return self._exhausted

    def _event(self, event_type: EventType, data: dict[str, Any]) -> Event:
        return Event(event_type, time.time(), data, camera_id=self._camera_id)

    def step(self) -> list[Event]:
        """Read one frame, run the pipeline, publish and return the events."""
        if not self._opened:
            self._opened = self._source.open()
            if not self._opened:
                self._status = CameraRuntimeStatus.ERROR
                return []
        frame = self._source.read()
        if frame is None:
            self._exhausted = True
            return []

        detections = self._detector.detect(frame)
        tracks = self._tracker.update(detections)
        timestamp = time.time()
        zone_events = self._zone_engine.update(tracks, timestamp)
        completed = self._dwell.update(zone_events)

        events = self._build_events(tracks, zone_events, completed)
        for event in events:
            self._publish(event)
        return events

    def _build_events(self, tracks, zone_events, completed) -> list[Event]:
        events: list[Event] = []

        for track in tracks:
            if track.state is TrackState.NEW:
                events.append(
                    self._event(
                        EventType.TRACK_CREATED,
                        {"track_id": track.track_id, "class_name": track.class_name},
                    )
                )
            else:
                events.append(self._event(EventType.TRACK_UPDATED, {"track_id": track.track_id}))

        for zone_event in zone_events:
            is_enter = zone_event.event_type is ZoneEventType.ENTER
            event_type = EventType.ZONE_ENTER if is_enter else EventType.ZONE_EXIT
            events.append(
                self._event(
                    event_type,
                    {
                        "track_id": zone_event.track_id,
                        "zone_id": zone_event.zone_id,
                        "timestamp": zone_event.timestamp,
                    },
                )
            )
            if is_enter:
                events.append(
                    self._event(
                        EventType.DWELL_STARTED,
                        {
                            "track_id": zone_event.track_id,
                            "zone_id": zone_event.zone_id,
                            "enter_time": zone_event.timestamp,
                        },
                    )
                )

        for session in completed:
            events.append(
                self._event(
                    EventType.DWELL_COMPLETED,
                    {
                        "track_id": session.track_id,
                        "zone_id": session.zone_id,
                        "enter_time": session.enter_time,
                        "exit_time": session.exit_time,
                        "duration": session.duration,
                    },
                )
            )

        return events

    def run(self, stop_event, poll_interval: float = 0.0) -> None:
        """Run until stopped; isolated so a failure here never crashes the app."""
        self._status = CameraRuntimeStatus.STARTING
        if not self._source.open():
            self._status = CameraRuntimeStatus.ERROR
            return
        self._opened = True
        self._status = CameraRuntimeStatus.RUNNING
        try:
            while not stop_event.is_set():
                try:
                    self.step()
                except Exception:
                    logger.exception("pipeline error for camera %s", self._camera_id)
                    self._status = CameraRuntimeStatus.ERROR
                    break
                if self._exhausted:
                    break
                if poll_interval > 0:
                    stop_event.wait(poll_interval)
        finally:
            self._source.close()
            if self._status is not CameraRuntimeStatus.ERROR:
                self._status = CameraRuntimeStatus.STOPPED
