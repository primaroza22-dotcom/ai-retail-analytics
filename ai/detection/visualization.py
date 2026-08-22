"""Utilities for drawing detections on frames."""

from __future__ import annotations

import numpy as np

from .types import Detection


def draw_detections(
    frame: np.ndarray,
    detections: list[Detection],
    *,
    color: tuple[int, int, int] = (0, 255, 0),
    thickness: int = 2,
) -> np.ndarray:
    """Return a copy of ``frame`` with detection boxes and labels drawn on it."""
    import cv2

    annotated = frame.copy()
    for detection in detections:
        bbox = detection.bbox
        x1, y1 = int(bbox.x1), int(bbox.y1)
        x2, y2 = int(bbox.x2), int(bbox.y2)
        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, thickness)
        label = f"{detection.class_name} {detection.confidence:.2f}"
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
