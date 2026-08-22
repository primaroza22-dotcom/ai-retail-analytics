"""Unit tests for detection types and the raw-output parser."""

import numpy as np

from ai.detection.detector import boxes_to_detections
from ai.detection.types import BBox, Detection

NAMES = {0: "person", 1: "bicycle"}


def test_bbox_valid() -> None:
    assert BBox(0, 0, 10, 10).is_valid() is True
    assert BBox(10, 10, 5, 5).is_valid() is False  # x2 <= x1
    assert BBox(-1, 0, 10, 10).is_valid() is False  # negative coordinate


def test_detection_to_dict_schema() -> None:
    det = Detection(
        class_id=0,
        class_name="person",
        confidence=0.94,
        bbox=BBox(120, 80, 320, 500),
    )
    assert det.to_dict() == {
        "class_id": 0,
        "class_name": "person",
        "confidence": 0.94,
        "bbox": {"x1": 120, "y1": 80, "x2": 320, "y2": 500},
    }


def test_parser_filters_non_person() -> None:
    xyxy = np.array([[10, 10, 50, 50], [20, 20, 60, 60]])
    cls = np.array([0, 1])
    conf = np.array([0.9, 0.9])
    detections = boxes_to_detections(
        xyxy, cls, conf, NAMES, confidence_threshold=0.4, allowed_class_ids={0}
    )
    assert len(detections) == 1
    assert detections[0].class_name == "person"


def test_parser_applies_threshold() -> None:
    detections = boxes_to_detections(
        np.array([[10, 10, 50, 50]]),
        np.array([0]),
        np.array([0.2]),
        NAMES,
        confidence_threshold=0.4,
        allowed_class_ids={0},
    )
    assert detections == []


def test_parser_sorts_by_confidence_desc() -> None:
    xyxy = np.array([[0, 0, 10, 10], [0, 0, 20, 20]])
    cls = np.array([0, 0])
    conf = np.array([0.5, 0.9])
    detections = boxes_to_detections(
        xyxy, cls, conf, NAMES, confidence_threshold=0.4, allowed_class_ids={0}
    )
    assert [d.confidence for d in detections] == [0.9, 0.5]


def test_parser_outputs_valid_schema() -> None:
    detections = boxes_to_detections(
        np.array([[5, 5, 50, 80]]),
        np.array([0]),
        np.array([0.7]),
        NAMES,
        confidence_threshold=0.4,
        allowed_class_ids={0},
    )
    for detection in detections:
        assert detection.class_id == 0
        assert detection.class_name == "person"
        assert 0.0 <= detection.confidence <= 1.0
        assert detection.bbox.is_valid()
