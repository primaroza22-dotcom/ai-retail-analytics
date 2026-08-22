"""Centralized detector configuration."""

from __future__ import annotations

from dataclasses import dataclass

from .exceptions import DetectionError

# COCO dataset class id for "person".
PERSON_CLASS_ID = 0


@dataclass(frozen=True)
class DetectionConfig:
    model_path: str = "models/yolov8n.pt"
    confidence_threshold: float = 0.40
    device: str = "cpu"
    person_class_id: int = PERSON_CLASS_ID
    imgsz: int = 640

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence_threshold <= 1.0:
            raise DetectionError(
                f"confidence_threshold must be in [0, 1], got {self.confidence_threshold}"
            )
