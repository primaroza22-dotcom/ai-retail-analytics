"""Structured tracking result types.

A track id is only a temporary identity within a single tracking session. It is
not a human identity and never encodes personal information.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from ai.detection.types import BBox


class TrackState(str, Enum):
    """Lifecycle state of a track."""

    NEW = "new"
    ACTIVE = "active"
    LOST = "lost"
    REMOVED = "removed"


@dataclass(frozen=True)
class TrackResult:
    """A tracked object with a temporary tracking id."""

    track_id: int
    class_id: int
    class_name: str
    confidence: float
    bbox: BBox
    state: TrackState

    @property
    def center_x(self) -> float:
        return (self.bbox.x1 + self.bbox.x2) / 2

    @property
    def center_y(self) -> float:
        return (self.bbox.y1 + self.bbox.y2) / 2

    def to_dict(self) -> dict[str, Any]:
        return {
            "track_id": self.track_id,
            "class_id": self.class_id,
            "class_name": self.class_name,
            "confidence": self.confidence,
            "bbox": self.bbox.to_dict(),
            "state": self.state.value,
        }
