"""HTTP route handlers.

Routes only translate HTTP requests into service calls and serialize results.
No business logic or database access lives here.
"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy import text

from .deps import get_analytics_service, get_zone_service
from .schemas import (
    AnalyticsSummary,
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
from .services import AnalyticsService, ZoneService

router = APIRouter()


@router.get("/health", tags=["system"])
def health(request: Request) -> JSONResponse:
    """Liveness + database connectivity check (no credentials leaked)."""
    try:
        with request.app.state.engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception:
        return JSONResponse(status_code=503, content={"status": "error"})
    return JSONResponse(status_code=200, content={"status": "ok"})


# --- Zones ---


@router.post(
    "/zones",
    response_model=ZoneRead,
    status_code=status.HTTP_201_CREATED,
    tags=["zones"],
)
def create_zone(payload: ZoneCreate, zone_service=Depends(get_zone_service)) -> ZoneRead:
    return zone_service.create(payload)


@router.get("/zones", response_model=list[ZoneRead], tags=["zones"])
def list_zones(zone_service=Depends(get_zone_service)) -> list[ZoneRead]:
    return zone_service.list()


@router.put("/zones/{zone_id}", response_model=ZoneRead, tags=["zones"])
def update_zone(
    zone_id: str,
    payload: ZoneUpdate,
    zone_service=Depends(get_zone_service),
) -> ZoneRead:
    return zone_service.update(zone_id, payload)


# --- Events ---


@router.post(
    "/events",
    response_model=list[ZoneEventRead],
    status_code=status.HTTP_201_CREATED,
    tags=["analytics"],
)
def record_events(
    payload: list[ZoneEventCreate], service: AnalyticsService = Depends(get_analytics_service)
) -> list[ZoneEventRead]:
    return service.record_events(payload)


@router.get("/events", response_model=EventListResponse, tags=["analytics"])
def list_events(
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    zone_id: str | None = None,
    event_type: str | None = None,
    track_id: int | None = None,
    start_time: float | None = None,
    end_time: float | None = None,
    service: AnalyticsService = Depends(get_analytics_service),
) -> EventListResponse:
    return service.list_events(
        limit=limit,
        offset=offset,
        zone_id=zone_id,
        event_type=event_type,
        track_id=track_id,
        start_time=start_time,
        end_time=end_time,
    )


# --- Dwell sessions ---


@router.post(
    "/dwell-sessions",
    response_model=list[DwellSessionRead],
    status_code=status.HTTP_201_CREATED,
    tags=["analytics"],
)
def record_dwell_sessions(
    payload: list[DwellSessionCreate],
    service: AnalyticsService = Depends(get_analytics_service),
) -> list[DwellSessionRead]:
    return service.record_sessions(payload)


# --- Analytics ---


@router.get("/analytics/dwell", response_model=DwellListResponse, tags=["analytics"])
def dwell_sessions(
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    zone_id: str | None = None,
    track_id: int | None = None,
    status: Literal["ongoing", "completed"] | None = None,
    start_time: float | None = None,
    end_time: float | None = None,
    min_duration: float | None = None,
    max_duration: float | None = None,
    now: float | None = None,
    service: AnalyticsService = Depends(get_analytics_service),
) -> DwellListResponse:
    return service.list_dwell_sessions(
        limit=limit,
        offset=offset,
        zone_id=zone_id,
        track_id=track_id,
        status=status,
        start_time=start_time,
        end_time=end_time,
        min_duration=min_duration,
        max_duration=max_duration,
        now=now,
    )


@router.get("/analytics/summary", response_model=AnalyticsSummary, tags=["analytics"])
def analytics_summary(
    start_time: float | None = None,
    end_time: float | None = None,
    service: AnalyticsService = Depends(get_analytics_service),
) -> AnalyticsSummary:
    return service.summary(start_time, end_time)


@router.get("/analytics/zones", response_model=list[ZoneAnalytics], tags=["analytics"])
def zone_analytics(
    start_time: float | None = None,
    end_time: float | None = None,
    service: AnalyticsService = Depends(get_analytics_service),
) -> list[ZoneAnalytics]:
    return service.zone_analytics(start_time, end_time)


@router.get(
    "/analytics/zones/ranking",
    response_model=list[ZoneRanking],
    tags=["analytics"],
)
def zone_ranking(
    metric: Literal["average_dwell", "total_dwell"] = "average_dwell",
    start_time: float | None = None,
    end_time: float | None = None,
    service: AnalyticsService = Depends(get_analytics_service),
) -> list[ZoneRanking]:
    return service.zone_ranking(metric, start_time, end_time)


@router.get("/analytics/daily", response_model=list[DailyAnalytics], tags=["analytics"])
def daily_analytics(
    start_time: float | None = None,
    end_time: float | None = None,
    service: AnalyticsService = Depends(get_analytics_service),
) -> list[DailyAnalytics]:
    return service.daily(start_time, end_time)
