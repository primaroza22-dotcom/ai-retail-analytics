"""Structured detection result types."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class BBox:
    """Axis-aligned bounding box with top-left and bottom-right corners."""

    x1: float
    y1: float
    x2: float
    y2: float

    def is_valid(self) -> bool:
        return (
            self.x2 > self.x1
            and self.y2 > self.y1
            and self.x1 >= 0
            and self.y1 >= 0
        )

    def to_dict(self) -> dict[str, float]:
        return {"x1": self.x1, "y1": self.y1, "x2": self.x2, "y2": self.y2}


@dataclass(frozen=True)
class Detection:
    """A single object detection result."""

    class_id: int
    class_name: str
    confidence: float
    bbox: BBox

    def to_dict(self) -> dict[str, Any]:
        return {
            "class_id": self.class_id,
            "class_name": self.class_name,
            "confidence": self.confidence,
            "bbox": self.bbox.to_dict(),
        }
