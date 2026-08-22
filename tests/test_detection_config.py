"""Unit tests for the centralized detector configuration."""

import pytest

from ai.detection.config import PERSON_CLASS_ID, DetectionConfig
from ai.detection.exceptions import DetectionError


def test_default_config() -> None:
    config = DetectionConfig()
    assert config.confidence_threshold == 0.40
    assert config.device == "cpu"
    assert config.person_class_id == 0
    assert PERSON_CLASS_ID == 0


def test_config_rejects_invalid_threshold() -> None:
    with pytest.raises(DetectionError):
        DetectionConfig(confidence_threshold=1.5)
    with pytest.raises(DetectionError):
        DetectionConfig(confidence_threshold=-0.1)
