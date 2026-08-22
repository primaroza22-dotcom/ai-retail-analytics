"""Unit tests for detector error handling (no model required)."""

import numpy as np
import pytest

from ai.detection.detector import validate_frame
from ai.detection.exceptions import DetectionError
from ai.detection.detector import YOLODetector


def test_detector_initializes_without_loading() -> None:
    detector = YOLODetector()
    assert detector.is_loaded is False


def test_validate_frame_accepts_array() -> None:
    validate_frame(np.zeros((10, 10, 3), dtype=np.uint8))


def test_validate_frame_rejects_non_array() -> None:
    with pytest.raises(DetectionError):
        validate_frame("not an array")  # type: ignore[arg-type]


def test_validate_frame_rejects_empty() -> None:
    with pytest.raises(DetectionError):
        validate_frame(np.array([]))
