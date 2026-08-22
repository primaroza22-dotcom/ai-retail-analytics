"""YOLO-based person detector.

The detector is deliberately decoupled from the camera layer: it only receives
a numpy frame and returns a structured list of detections. It never opens
cameras, touches the database, or talks to the frontend.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import numpy as np

from .config import DetectionConfig
from .exceptions import DetectionError
from .types import BBox, Detection


def validate_frame(frame: np.ndarray) -> None:
    """Raise DetectionError if ``frame`` is not a usable image array."""
    if not isinstance(frame, np.ndarray):
        raise DetectionError(
            f"frame must be a numpy.ndarray, got {type(frame).__name__}"
        )
    if frame.size == 0:
        raise DetectionError("frame is empty")


def boxes_to_detections(
    xyxy: np.ndarray,
    class_ids: np.ndarray,
    confidences: np.ndarray,
    names: Mapping[int, str],
    *,
    confidence_threshold: float,
    allowed_class_ids: set[int],
) -> list[Detection]:
    """Convert raw model outputs into a clean, sorted list of Detection objects."""
    detections: list[Detection] = []
    for box, class_id_raw, confidence_raw in zip(xyxy, class_ids, confidences):
        class_id = int(class_id_raw)
        confidence = float(confidence_raw)
        if class_id not in allowed_class_ids:
            continue
        if confidence < confidence_threshold:
            continue
        x1, y1, x2, y2 = (float(value) for value in box)
        detections.append(
            Detection(
                class_id=class_id,
                class_name=names.get(class_id, str(class_id)),
                confidence=confidence,
                bbox=BBox(x1=x1, y1=y1, x2=x2, y2=y2),
            )
        )
    detections.sort(key=lambda d: d.confidence, reverse=True)
    return detections


class YOLODetector:
    """Loads a YOLO model and runs person detection on single frames."""

    def __init__(self, config: DetectionConfig | None = None) -> None:
        self.config = config or DetectionConfig()
        self._model: Any = None

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    def load(self) -> None:
        from ultralytics import YOLO  # lazy import

        model_path = Path(self.config.model_path).resolve()
        model_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self._model = YOLO(str(model_path))
        except Exception as exc:
            raise DetectionError(
                f"Failed to load YOLO model from {model_path}: {exc}"
            ) from exc

    def detect(self, frame: np.ndarray) -> list[Detection]:
        """Run person detection on a single frame and return structured results."""
        self._ensure_loaded()
        validate_frame(frame)

        try:
            results = self._model.predict(
                source=frame,
                conf=self.config.confidence_threshold,
                device=self.config.device,
                imgsz=self.config.imgsz,
                verbose=False,
            )
        except Exception as exc:
            raise DetectionError(f"YOLO inference failed: {exc}") from exc

        result = results[0]
        boxes = result.boxes
        if boxes is None or len(boxes) == 0:
            return []

        xyxy = boxes.xyxy.cpu().numpy()
        class_ids = boxes.cls.cpu().numpy()
        confidences = boxes.conf.cpu().numpy()
        return boxes_to_detections(
            xyxy,
            class_ids,
            confidences,
            names=self._model.names,
            confidence_threshold=self.config.confidence_threshold,
            allowed_class_ids={self.config.person_class_id},
        )

    def _ensure_loaded(self) -> None:
        if self._model is None:
            self.load()
