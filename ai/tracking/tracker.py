"""ByteTrack-based object tracker.

The tracker is decoupled from the camera and detector layers: it accepts a list
of Detection objects and returns TrackResult objects with a temporary track id.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ai.detection.types import BBox, Detection

from .exceptions import TrackingError
from .types import TrackResult, TrackState


@dataclass(frozen=True)
class TrackingConfig:
    """Configuration for the ByteTrack backend and track lifecycle."""

    track_thresh: float = 0.45
    match_thresh: float = 0.8
    min_conf: float = 0.1
    max_lost_frames: int = 25
    frame_rate: int = 30


@dataclass
class _Track:
    class_id: int
    class_name: str
    confidence: float
    bbox: BBox
    state: TrackState
    lost_count: int = 0


class ObjectTracker:
    """Tracks detections across frames and manages track lifecycle."""

    def __init__(self, config: TrackingConfig | None = None) -> None:
        self.config = config or TrackingConfig()
        self._backend = self._create_backend()
        self._tracks: dict[int, _Track] = {}
        self._placeholder = np.zeros((1, 1, 3), dtype=np.uint8)

    def _create_backend(self):
        from boxmot.trackers.bbox.bytetrack import ByteTrack  # lazy import

        try:
            return ByteTrack(
                min_conf=self.config.min_conf,
                track_thresh=self.config.track_thresh,
                match_thresh=self.config.match_thresh,
                track_buffer=self.config.max_lost_frames,
                frame_rate=self.config.frame_rate,
            )
        except Exception as exc:
            raise TrackingError(f"Failed to initialize ByteTrack backend: {exc}") from exc

    @property
    def track_ids(self) -> list[int]:
        return sorted(self._tracks)

    def states(self) -> dict[int, TrackState]:
        """Return the current lifecycle state of every known (non-removed) track."""
        return {track_id: track.state for track_id, track in self._tracks.items()}

    def reset(self) -> None:
        self._tracks.clear()
        self._backend = self._create_backend()

    def update(self, detections: list[Detection]) -> list[TrackResult]:
        """Update tracks with one frame of detections and return active tracks."""
        self._validate_detections(detections)
        dets = self._to_detection_array(detections)
        active_ids = self._associate(dets, detections)
        self._update_lifecycle(active_ids)
        return self._active_results()

    @staticmethod
    def _validate_detections(detections: list[Detection]) -> None:
        for detection in detections:
            if not detection.bbox.is_valid():
                raise TrackingError(f"Invalid detection bbox: {detection.bbox}")

    @staticmethod
    def _to_detection_array(detections: list[Detection]) -> np.ndarray:
        if not detections:
            return np.empty((0, 6), dtype=np.float32)
        return np.array(
            [
                [d.bbox.x1, d.bbox.y1, d.bbox.x2, d.bbox.y2, d.confidence, d.class_id]
                for d in detections
            ],
            dtype=np.float32,
        )

    def _associate(self, dets: np.ndarray, detections: list[Detection]) -> set[int]:
        outputs = self._backend.update(dets, self._placeholder)
        names = {d.class_id: d.class_name for d in detections}
        active: set[int] = set()
        for xyxy, track_id, confidence, class_id in zip(
            outputs.xyxy, outputs.id, outputs.conf, outputs.cls
        ):
            track_id = int(track_id)
            class_id = int(class_id)
            bbox = BBox(
                x1=float(xyxy[0]),
                y1=float(xyxy[1]),
                x2=float(xyxy[2]),
                y2=float(xyxy[3]),
            )
            class_name = names.get(class_id, str(class_id))
            track = self._tracks.get(track_id)
            if track is None:
                self._tracks[track_id] = _Track(
                    class_id=class_id,
                    class_name=class_name,
                    confidence=float(confidence),
                    bbox=bbox,
                    state=TrackState.NEW,
                )
            else:
                track.class_id = class_id
                track.class_name = class_name
                track.confidence = float(confidence)
                track.bbox = bbox
                track.state = TrackState.ACTIVE
                track.lost_count = 0
            active.add(track_id)
        return active

    def _update_lifecycle(self, active_ids: set[int]) -> None:
        for track_id in list(self._tracks):
            if track_id in active_ids:
                continue
            track = self._tracks[track_id]
            track.lost_count += 1
            track.state = TrackState.LOST
            if track.lost_count > self.config.max_lost_frames:
                track.state = TrackState.REMOVED
                del self._tracks[track_id]

    def _active_results(self) -> list[TrackResult]:
        results: list[TrackResult] = []
        for track_id in sorted(self._tracks):
            track = self._tracks[track_id]
            if track.state in (TrackState.NEW, TrackState.ACTIVE):
                results.append(
                    TrackResult(
                        track_id=track_id,
                        class_id=track.class_id,
                        class_name=track.class_name,
                        confidence=track.confidence,
                        bbox=track.bbox,
                        state=track.state,
                    )
                )
        return results
