"""Real-time subsystem (Sprint 10).

Event bus + WebSocket connection manager, decoupled from the detection,
tracking, analytics, and database layers.
"""

from .bus import EventBus
from .events import Event, EventType
from .manager import ConnectionManager

__all__ = [
    "ConnectionManager",
    "Event",
    "EventBus",
    "EventType",
]
