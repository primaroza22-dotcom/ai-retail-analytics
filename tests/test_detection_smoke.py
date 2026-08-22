"""Smoke tests: run the real YOLO model on a bundled image (no CCTV needed)."""

import numpy as np
import pytest


def _load_bus_image() -> np.ndarray:
    import cv2

    from ultralytics.utils import ASSETS

    image = cv2.imread(str(ASSETS / "bus.jpg"))
    assert image is not None, "could not load the bundled ultralytics bus.jpg asset"
    return image


@pytest.mark.smoke
def test_model_loads(detector) -> None:
    assert detector.is_loaded is True


@pytest.mark.smoke
def test_detects_person_on_bus_image(detector) -> None:
    detections = detector.detect(_load_bus_image())
    assert len(detections) > 0, "expected at least one person detection"
    assert all(d.class_id == 0 for d in detections)
    assert all(d.class_name == "person" for d in detections)


@pytest.mark.smoke
def test_detections_have_valid_schema(detector) -> None:
    detections = detector.detect(_load_bus_image())
    assert detections, "expected non-empty detections"
    for detection in detections:
        assert 0.0 <= detection.confidence <= 1.0
        assert detection.bbox.is_valid()
