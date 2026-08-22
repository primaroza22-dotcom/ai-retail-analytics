"""Camera input subsystem (Sprint 2): RTSP / ONVIF.

Provides camera configuration, RTSP stream reading with reconnect support,
a multi-camera manager, and an ONVIF foundation. This package is deliberately
independent of YOLO, tracking, analytics, and the web layer.
"""

from .config import CameraConfig, CameraConfigStore
from .exceptions import CameraConfigError, CameraError
from .manager import CameraManager
from .onvif import OnvifClient, OnvifDeviceInfo, build_rtsp_url
from .stream import CameraStream, StreamStatus, default_capture_factory

__all__ = [
    "CameraConfig",
    "CameraConfigError",
    "CameraConfigStore",
    "CameraError",
    "CameraManager",
    "CameraStream",
    "OnvifClient",
    "OnvifDeviceInfo",
    "StreamStatus",
    "build_rtsp_url",
    "default_capture_factory",
]
