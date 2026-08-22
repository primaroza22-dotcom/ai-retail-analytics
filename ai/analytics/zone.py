"""Zone / ROI definitions and the zone engine.

Coordinate system: image coordinates with origin (0, 0) at the top-left,
x growing horizontally (right) and y growing vertically (down). A track's
position is its bounding-box center point ``(center_x, center_y)``.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from ai.tracking.types import TrackResult

from .exceptions import AnalyticsError

_EPS = 1e-9


def _on_segment(px: float, py: float, x1: float, y1: float, x2: float, y2: float) -> bool:
    cross = (py - y1) * (x2 - x1) - (px - x1) * (y2 - y1)
    if abs(cross) > _EPS:
        return False
    return (
        min(x1, x2) - _EPS <= px <= max(x1, x2) + _EPS
        and min(y1, y2) - _EPS <= py <= max(y1, y2) + _EPS
    )


def point_in_polygon(x: float, y: float, polygon: tuple[tuple[float, float], ...]) -> bool:
    """Ray-casting point-in-polygon test.

    A point lying exactly on an edge or vertex is considered inside (a closed
    polygon). ``polygon`` is an ordered sequence of ``(x, y)`` vertices.
    """
    inside = False
    n = len(polygon)
    j = n - 1
    for i in range(n):
        x1, y1 = polygon[j]
        x2, y2 = polygon[i]
        if _on_segment(x, y, x1, y1, x2, y2):
            return True
        if (y1 > y) != (y2 > y):
            x_intersect = (x2 - x1) * (y - y1) / (y2 - y1) + x1
            if x < x_intersect:
                inside = not inside
        j = i
    return inside


@dataclass(frozen=True)
class Zone:
    """A polygonal region of interest."""

    zone_id: str
    name: str
    polygon: tuple[tuple[float, float], ...]
    enabled: bool = True

    def __post_init__(self) -> None:
        normalized = tuple(tuple(map(float, point)) for point in self.polygon)
        if len(normalized) < 3:
            raise AnalyticsError(
                f"Zone '{self.zone_id}' must define a polygon with at least 3 points"
            )
        object.__setattr__(self, "polygon", normalized)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Zone:
        return cls(
            zone_id=data["zone_id"],
            name=data.get("name", data["zone_id"]),
            polygon=tuple(tuple(point) for point in data["polygon"]),
            enabled=data.get("enabled", True),
        )

    def contains(self, x: float, y: float) -> bool:
        return point_in_polygon(x, y, self.polygon)


class ZoneEventType(str, Enum):
    ENTER = "enter"
    EXIT = "exit"


@dataclass(frozen=True)
class ZoneMembership:
    """Per-frame membership of a track in a single zone."""

    track_id: int
    zone_id: str
    zone_name: str
    inside: bool
    timestamp: float


@dataclass(frozen=True)
class ZoneEvent:
    """A state change (ENTER / EXIT) for a track in a zone."""

    event_type: ZoneEventType
    track_id: int
    zone_id: str
    timestamp: float


class ZoneEngine:
    """Classifies tracks into zones and emits ENTER / EXIT events."""

    def __init__(self, zones: list[Zone]) -> None:
        self._zones = {zone.zone_id: zone for zone in zones}
        self._inside: dict[tuple[int, str], bool] = {}

    @property
    def zones(self) -> list[Zone]:
        return list(self._zones.values())

    def memberships(self, tracks: list[TrackResult], timestamp: float) -> list[ZoneMembership]:
        memberships: list[ZoneMembership] = []
        for track in tracks:
            for zone in self._zones.values():
                if not zone.enabled:
                    continue
                memberships.append(
                    ZoneMembership(
                        track_id=track.track_id,
                        zone_id=zone.zone_id,
                        zone_name=zone.name,
                        inside=zone.contains(track.center_x, track.center_y),
                        timestamp=timestamp,
                    )
                )
        return memberships

    def update(self, tracks: list[TrackResult], timestamp: float) -> list[ZoneEvent]:
        """Update per-zone state and return the ENTER/EXIT events for this frame."""
        memberships = self.memberships(tracks, timestamp)
        current = {(m.track_id, m.zone_id): m.inside for m in memberships}

        events: list[ZoneEvent] = []
        for key, inside in current.items():
            was_inside = self._inside.get(key, False)
            if inside and not was_inside:
                events.append(ZoneEvent(ZoneEventType.ENTER, key[0], key[1], timestamp))
            elif not inside and was_inside:
                events.append(ZoneEvent(ZoneEventType.EXIT, key[0], key[1], timestamp))
        self._inside = current
        return events

    def reset(self) -> None:
        self._inside.clear()
