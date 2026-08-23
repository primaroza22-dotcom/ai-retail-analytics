"""Real-time event vocabulary shared across the backend.

Events are JSON-serializable, versionable, and independent from SQLAlchemy ORM
objects. The same vocabulary is mirrored in the Next.js frontend.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class EventType(str, Enum):
    """Centralized event types for the real-time event bus."""

    CONNECTION = "connection"
    HEARTBEAT = "heartbeat"
    DETECTION = "detection"
    TRACK_CREATED = "track_created"
    TRACK_UPDATED = "track_updated"
    ZONE_ENTER = "zone_enter"
    ZONE_EXIT = "zone_exit"
    DWELL_STARTED = "dwell_started"
    DWELL_UPDATED = "dwell_updated"
    DWELL_COMPLETED = "dwell_completed"
    ANALYTICS_UPDATE = "analytics_update"
    SYSTEM_STATUS = "system_status"
    CAMERA_CONNECTED = "camera_connected"
    CAMERA_DISCONNECTED = "camera_disconnected"
    CAMERA_ERROR = "camera_error"
    CAMERA_RECONNECTING = "camera_reconnecting"
    TRANSACTION_CREATED = "transaction_created"
    TRANSACTION_UPDATED = "transaction_updated"
    TRANSACTION_CANCELLED = "transaction_cancelled"
    TRANSACTION_REFUNDED = "transaction_refunded"
    FORECAST_UPDATED = "forecast_updated"
    ANALYTICS_INSIGHT = "analytics_insight"
    ANOMALY_DETECTED = "anomaly_detected"


@dataclass(frozen=True)
class Event:
    """A structured, versionable event envelope."""

    type: EventType
    timestamp: float
    data: dict[str, Any] = field(default_factory=dict)
    version: int = 1
    camera_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "type": self.type.value,
            "version": self.version,
            "timestamp": self.timestamp,
            "data": self.data,
        }
        if self.camera_id is not None:
            payload["camera_id"] = self.camera_id
        return payload
