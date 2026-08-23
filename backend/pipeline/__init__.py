"""Multi-camera pipeline (Sprint 11).

Orchestrates one isolated worker per camera. The worker composes a source,
detector, tracker, zone engine, and dwell analyzer and publishes camera-scoped
events to the real-time event bus.
"""

from .manager import PipelineManager
from .source import CameraRuntimeStatus, CameraSource, TestCameraSource
from .worker import CameraWorker

__all__ = [
    "CameraRuntimeStatus",
    "CameraSource",
    "CameraWorker",
    "PipelineManager",
    "TestCameraSource",
]
