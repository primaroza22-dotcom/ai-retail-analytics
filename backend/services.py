"""Business-logic services.

Services contain the domain rules (uniqueness, camera/zone existence, duration
derivation, filtering, pagination, aggregation, ranking) and delegate
persistence to repositories. Route handlers only translate HTTP into service
calls and back.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone

from .exceptions import ConflictError, NotFoundError
from .models import STATUS_COMPLETED, STATUS_ONGOING, Camera, DwellSession, Zone, ZoneEvent
from .realtime import Event, EventBus, EventType
from .repositories import CameraRepository, DwellRepository, EventRepository, ZoneRepository
from .schemas import (
    AnalyticsSummary,
    CameraCreate,
    CameraRead,
    CameraUpdate,
    DailyAnalytics,
    DwellListResponse,
    DwellSessionCreate,
    DwellSessionRead,
    EventListResponse,
    ZoneAnalytics,
    ZoneCreate,
    ZoneEventCreate,
    ZoneEventRead,
    ZoneRanking,
    ZoneRead,
    ZoneUpdate,
)


class CameraService:
    """Manages the camera registry."""

    def __init__(self, cameras: CameraRepository) -> None:
        self._cameras = cameras

    def create(self, data: CameraCreate) -> CameraRead:
        if self._cameras.get(data.id) is not None:
            raise ConflictError(f"Camera already exists: {data.id}")
        camera = Camera(
            id=data.id,
            name=data.name,
            description=data.description,
            source_type=data.source_type,
            source_url=data.source_url,
            enabled=data.enabled,
            location=data.location,
        )
        self._cameras.add(camera)
        return CameraRead.model_validate(camera)

    def list(self) -> list[CameraRead]:
        return [CameraRead.model_validate(camera) for camera in self._cameras.list()]

    def get(self, camera_id: str) -> CameraRead:
        return CameraRead.model_validate(self._require(camera_id))

    def update(self, camera_id: str, data: CameraUpdate) -> CameraRead:
        camera = self._require(camera_id)
        if data.name is not None:
            camera.name = data.name
        if data.description is not None:
            camera.description = data.description
        if data.source_type is not None:
            camera.source_type = data.source_type
        if data.source_url is not None:
            camera.source_url = data.source_url
        if data.enabled is not None:
            camera.enabled = data.enabled
        if data.location is not None:
            camera.location = data.location
        return CameraRead.model_validate(camera)

    def disable(self, camera_id: str) -> CameraRead:
        """Soft-delete a camera (preserves historical references)."""
        camera = self._require(camera_id)
        camera.enabled = False
        return CameraRead.model_validate(camera)

    def _require(self, camera_id: str) -> Camera:
        camera = self._cameras.get(camera_id)
        if camera is None:
            raise NotFoundError(f"Unknown camera: {camera_id}")
        return camera


class ZoneService:
    """Manages zone configuration."""

    def __init__(
        self,
        zones: ZoneRepository,
        cameras: CameraRepository | None = None,
    ) -> None:
        self._zones = zones
        self._cameras = cameras

    def _require_camera(self, camera_id: str | None) -> None:
        if camera_id is not None and self._cameras is not None:
            if self._cameras.get(camera_id) is None:
                raise NotFoundError(f"Unknown camera: {camera_id}")

    def create(self, data: ZoneCreate) -> ZoneRead:
        if self._zones.get(data.id) is not None:
            raise ConflictError(f"Zone already exists: {data.id}")
        self._require_camera(data.camera_id)
        zone = Zone(
            id=data.id,
            name=data.name,
            camera_id=data.camera_id,
            polygon=data.polygon,
            enabled=data.enabled,
        )
        self._zones.add(zone)
        return ZoneRead.model_validate(zone)

    def list(self, camera_id: str | None = None) -> list[ZoneRead]:
        return [ZoneRead.model_validate(zone) for zone in self._zones.list(camera_id)]

    def update(self, zone_id: str, data: ZoneUpdate) -> ZoneRead:
        zone = self._zones.get(zone_id)
        if zone is None:
            raise NotFoundError(f"Unknown zone: {zone_id}")
        if data.camera_id is not None:
            self._require_camera(data.camera_id)
            zone.camera_id = data.camera_id
        if data.name is not None:
            zone.name = data.name
        if data.polygon is not None:
            zone.polygon = data.polygon
        if data.enabled is not None:
            zone.enabled = data.enabled
        return ZoneRead.model_validate(zone)


class AnalyticsService:
    """Records events/sessions and derives dwell/occupancy aggregates."""

    def __init__(
        self,
        zones: ZoneRepository,
        events: EventRepository,
        dwell: DwellRepository,
        bus: EventBus | None = None,
    ) -> None:
        self._zones = zones
        self._events = events
        self._dwell = dwell
        self._bus = bus

    def _get_zone(self, zone_id: str) -> Zone:
        zone = self._zones.get(zone_id)
        if zone is None:
            raise NotFoundError(f"Unknown zone: {zone_id}")
        return zone

    def _publish(self, event_type: EventType, data: dict, camera_id: str | None) -> None:
        if self._bus is not None:
            self._bus.publish(Event(event_type, time.time(), data, camera_id=camera_id))

    # --- Events ---

    def record_events(self, items: list[ZoneEventCreate]) -> list[ZoneEventRead]:
        models = []
        for item in items:
            zone = self._get_zone(item.zone_id)
            models.append(
                ZoneEvent(
                    camera_id=zone.camera_id,
                    track_id=item.track_id,
                    zone_id=item.zone_id,
                    event_type=item.event_type,
                    timestamp=item.timestamp,
                )
            )
        self._events.add_many(models)
        for model in models:
            event_type = (
                EventType.ZONE_ENTER if model.event_type == "enter" else EventType.ZONE_EXIT
            )
            self._publish(
                event_type,
                {
                    "track_id": model.track_id,
                    "zone_id": model.zone_id,
                    "timestamp": model.timestamp,
                },
                model.camera_id,
            )
        return [ZoneEventRead.model_validate(model) for model in models]

    def list_events(
        self,
        *,
        limit: int,
        offset: int,
        zone_id: str | None,
        event_type: str | None,
        track_id: int | None,
        camera_id: str | None,
        start_time: float | None,
        end_time: float | None,
    ) -> EventListResponse:
        total = self._events.count(
            zone_id=zone_id,
            event_type=event_type,
            track_id=track_id,
            camera_id=camera_id,
            start_time=start_time,
            end_time=end_time,
        )
        items = [
            ZoneEventRead.model_validate(event)
            for event in self._events.list(
                limit=limit,
                offset=offset,
                zone_id=zone_id,
                event_type=event_type,
                track_id=track_id,
                camera_id=camera_id,
                start_time=start_time,
                end_time=end_time,
            )
        ]
        return EventListResponse(items=items, total=total, limit=limit, offset=offset)

    # --- Dwell sessions ---

    def record_sessions(self, items: list[DwellSessionCreate]) -> list[DwellSessionRead]:
        models = []
        for item in items:
            zone = self._get_zone(item.zone_id)
            if item.exit_time is not None:
                status = STATUS_COMPLETED
                duration = item.exit_time - item.enter_time
            else:
                status = STATUS_ONGOING
                duration = None
            models.append(
                DwellSession(
                    camera_id=zone.camera_id,
                    track_id=item.track_id,
                    zone_id=item.zone_id,
                    enter_time=item.enter_time,
                    exit_time=item.exit_time,
                    duration=duration,
                    status=status,
                )
            )
        self._dwell.add_many(models)
        for model in models:
            if model.status == STATUS_ONGOING:
                self._publish(
                    EventType.DWELL_STARTED,
                    {
                        "track_id": model.track_id,
                        "zone_id": model.zone_id,
                        "enter_time": model.enter_time,
                    },
                    model.camera_id,
                )
            else:
                self._publish(
                    EventType.DWELL_COMPLETED,
                    {
                        "track_id": model.track_id,
                        "zone_id": model.zone_id,
                        "enter_time": model.enter_time,
                        "exit_time": model.exit_time,
                        "duration": model.duration,
                    },
                    model.camera_id,
                )
        return [self._to_read(model, item.enter_time) for model, item in zip(models, items)]

    @staticmethod
    def _to_read(session: DwellSession, now: float) -> DwellSessionRead:
        if session.status == STATUS_ONGOING:
            duration = max(0.0, now - session.enter_time)
        else:
            duration = session.duration
        return DwellSessionRead(
            id=session.id,
            camera_id=session.camera_id,
            track_id=session.track_id,
            zone_id=session.zone_id,
            enter_time=session.enter_time,
            exit_time=session.exit_time,
            duration=duration,
            status=session.status,
        )

    def list_dwell_sessions(
        self,
        *,
        limit: int,
        offset: int,
        zone_id: str | None,
        track_id: int | None,
        status: str | None,
        camera_id: str | None,
        start_time: float | None,
        end_time: float | None,
        min_duration: float | None,
        max_duration: float | None,
        now: float | None,
    ) -> DwellListResponse:
        reference_now = now if now is not None else time.time()
        total = self._dwell.count(
            zone_id=zone_id,
            track_id=track_id,
            status=status,
            camera_id=camera_id,
            start_time=start_time,
            end_time=end_time,
        )
        items = [
            self._to_read(session, reference_now)
            for session in self._dwell.list(
                limit=limit,
                offset=offset,
                zone_id=zone_id,
                track_id=track_id,
                status=status,
                camera_id=camera_id,
                start_time=start_time,
                end_time=end_time,
                min_duration=min_duration,
                max_duration=max_duration,
            )
        ]
        return DwellListResponse(items=items, total=total, limit=limit, offset=offset)

    # --- Aggregates ---

    def summary(
        self, start_time: float | None, end_time: float | None, camera_id: str | None
    ) -> AnalyticsSummary:
        return AnalyticsSummary(**self._dwell.summary(start_time, end_time, camera_id))

    def zone_analytics(
        self, start_time: float | None, end_time: float | None, camera_id: str | None
    ) -> list[ZoneAnalytics]:
        return [
            ZoneAnalytics(**row) for row in self._dwell.by_zone(start_time, end_time, camera_id)
        ]

    def daily(
        self, start_time: float | None, end_time: float | None, camera_id: str | None
    ) -> list[DailyAnalytics]:
        result = []
        for row in self._dwell.daily(start_time, end_time, camera_id):
            date = datetime.fromtimestamp(row["day"], tz=timezone.utc).date().isoformat()
            result.append(
                DailyAnalytics(
                    date=date,
                    sessions=row["sessions"],
                    average_dwell_seconds=row["average_dwell_seconds"],
                    total_dwell_seconds=row["total_dwell_seconds"],
                )
            )
        return result

    def zone_ranking(
        self, metric: str, start_time: float | None, end_time: float | None, camera_id: str | None
    ) -> list[ZoneRanking]:
        rows = self._dwell.by_zone(start_time, end_time, camera_id)
        if metric == "total_dwell":
            key = lambda row: row["total_dwell_seconds"]  # noqa: E731
        else:
            key = lambda row: (row["average_dwell_seconds"] is not None, row["average_dwell_seconds"] or 0.0)  # noqa: E731

        ordered = sorted(rows, key=key, reverse=True)
        return [
            ZoneRanking(
                rank=index + 1,
                zone_id=row["zone_id"],
                zone_name=row["zone_name"],
                total_sessions=row["total_sessions"],
                average_dwell_seconds=row["average_dwell_seconds"],
                total_dwell_seconds=row["total_dwell_seconds"],
            )
            for index, row in enumerate(ordered)
        ]
