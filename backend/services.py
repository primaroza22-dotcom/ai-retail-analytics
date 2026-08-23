"""Business-logic services.

Services contain the domain rules (uniqueness, zone existence, duration
derivation, aggregation) and delegate persistence to repositories. Route
handlers only translate HTTP into service calls and back.
"""

from __future__ import annotations

from .exceptions import ConflictError, NotFoundError
from .models import DwellSession, Zone, ZoneEvent
from .repositories import DwellRepository, EventRepository, ZoneRepository
from .schemas import (
    DwellAnalyticsResponse,
    DwellSessionCreate,
    DwellSessionRead,
    ZoneCreate,
    ZoneDwellSummary,
    ZoneEventCreate,
    ZoneEventRead,
    ZoneRead,
)


class ZoneService:
    """Manages zone configuration."""

    def __init__(self, zones: ZoneRepository) -> None:
        self._zones = zones

    def create(self, data: ZoneCreate) -> ZoneRead:
        if self._zones.get(data.id) is not None:
            raise ConflictError(f"Zone already exists: {data.id}")
        zone = Zone(id=data.id, name=data.name, polygon=data.polygon, enabled=data.enabled)
        self._zones.add(zone)
        return ZoneRead.model_validate(zone)

    def list(self) -> list[ZoneRead]:
        return [ZoneRead.model_validate(zone) for zone in self._zones.list()]


class AnalyticsService:
    """Records analytics events and derives dwell/occupancy aggregates."""

    def __init__(
        self,
        zones: ZoneRepository,
        events: EventRepository,
        dwell: DwellRepository,
    ) -> None:
        self._zones = zones
        self._events = events
        self._dwell = dwell

    def _require_zone(self, zone_id: str) -> None:
        if self._zones.get(zone_id) is None:
            raise NotFoundError(f"Unknown zone: {zone_id}")

    def record_events(self, items: list[ZoneEventCreate]) -> list[ZoneEventRead]:
        models = []
        for item in items:
            self._require_zone(item.zone_id)
            models.append(
                ZoneEvent(
                    track_id=item.track_id,
                    zone_id=item.zone_id,
                    event_type=item.event_type,
                    timestamp=item.timestamp,
                )
            )
        self._events.add_many(models)
        return [ZoneEventRead.model_validate(model) for model in models]

    def record_sessions(self, items: list[DwellSessionCreate]) -> list[DwellSessionRead]:
        models = []
        for item in items:
            self._require_zone(item.zone_id)
            models.append(
                DwellSession(
                    track_id=item.track_id,
                    zone_id=item.zone_id,
                    enter_time=item.enter_time,
                    exit_time=item.exit_time,
                    duration=item.exit_time - item.enter_time,
                )
            )
        self._dwell.add_many(models)
        return [DwellSessionRead.model_validate(model) for model in models]

    def analytics(self) -> DwellAnalyticsResponse:
        sessions = [DwellSessionRead.model_validate(s) for s in self._dwell.list()]
        summary = [ZoneDwellSummary(**row) for row in self._dwell.summary_by_zone()]
        return DwellAnalyticsResponse(sessions=sessions, summary=summary)
