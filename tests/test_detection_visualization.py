"""Unit tests for the detection visualization utility."""

import numpy as np

from ai.detection.types import BBox, Detection
from ai.detection.visualization import draw_detections


def _frame() -> np.ndarray:
    return np.zeros((100, 100, 3), dtype=np.uint8)


def _detection() -> Detection:
    return Detection(class_id=0, class_name="person", confidence=0.9, bbox=BBox(10, 10, 50, 50))


def test_draw_detections_returns_same_shape() -> None:
    annotated = draw_detections(_frame(), [_detection()])
    assert annotated.shape == _frame().shape
    assert annotated.dtype == _frame().dtype


def test_draw_detections_does_not_modify_input() -> None:
    frame = _frame()
    original = frame.copy()
    draw_detections(frame, [_detection()])
    assert np.array_equal(frame, original)
