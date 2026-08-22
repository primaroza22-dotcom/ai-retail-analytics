"""YOLO person detection subsystem (Sprint 3).

Decoupled from the camera layer: the detector accepts a numpy frame and
returns a structured list of Detection objects. It does not open cameras,
access the database, or talk to the frontend.
"""

from .config import PERSON_CLASS_ID, DetectionConfig
from .detector import YOLODetector, boxes_to_detections, validate_frame
from .exceptions import DetectionError
from .types import BBox, Detection
from .visualization import draw_detections

__all__ = [
    "BBox",
    "Detection",
    "DetectionConfig",
    "DetectionError",
    "PERSON_CLASS_ID",
    "YOLODetector",
    "boxes_to_detections",
    "draw_detections",
    "validate_frame",
]
