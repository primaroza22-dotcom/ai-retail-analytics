"""Shared pytest fixtures."""

import pytest

from ai.detection import DetectionConfig, YOLODetector


@pytest.fixture(scope="session")
def detector() -> YOLODetector:
    """A loaded YOLO detector, shared across all model-based tests."""
    det = YOLODetector(DetectionConfig())
    det.load()
    return det
