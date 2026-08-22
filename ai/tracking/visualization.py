"""Utilities for drawing tracked objects on frames."""

from __future__ import annotations

import numpy as np

from .types import TrackResult


def draw_tracks(
    frame: np.ndarray,
    tracks: list[TrackResult],
    *,
    color: tuple[int, int, int] = (0, 255, 0),
    thickness: int = 2,
) -> np.ndarray:
    """Return a copy of ``frame`` with track boxes and their ids drawn on it."""
    import cv2

    annotated = frame.copy()
    for track in tracks:
        bbox = track.bbox
        x1, y1 = int(bbox.x1), int(bbox.y1)
        x2, y2 = int(bbox.x2), int(bbox.y2)
        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, thickness)
        label = f"ID {track.track_id}"
        cv2.putText(
            annotated,
            label,
            (x1, max(y1 - 5, 0)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            color,
            1,
            cv2.LINE_AA,
        )
    return annotated
