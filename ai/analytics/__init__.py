"""Zone / ROI and dwell-time analytics subsystem (Sprint 5).

Pure Python analytics that consume TrackResult objects and timestamps. It never
touches the camera, detector, tracker, database, or web layers.
"""

from .dwell_time import DwellSession, DwellTimeAnalyzer, OngoingDwell
from .exceptions import AnalyticsError
from .zone import (
    Zone,
    ZoneEngine,
    ZoneEvent,
    ZoneEventType,
    ZoneMembership,
    point_in_polygon,
)

__all__ = [
    "AnalyticsError",
    "DwellSession",
    "DwellTimeAnalyzer",
    "OngoingDwell",
    "Zone",
    "ZoneEngine",
    "ZoneEvent",
    "ZoneEventType",
    "ZoneMembership",
    "point_in_polygon",
]
