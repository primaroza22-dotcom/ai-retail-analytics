"""HTTP route handlers.

Routes only translate HTTP requests into service calls and serialize results.
No business logic or database access lives here.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy import text

from .deps import get_analytics_service, get_session, get_zone_service
from .schemas import (
    DwellAnalyticsResponse,
    DwellSessionCreate,
    DwellSessionRead,
    ZoneCreate,
    ZoneEventCreate,
    ZoneEventRead,
    ZoneRead,
)
from .services import AnalyticsService, ZoneService

router = APIRouter()


@router.get("/health", tags=["system"])
def health(session=Depends(get_session)) -> dict:
    session.execute(text("SELECT 1"))
    return {"status": "ok"}


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


@router.get(
    "/analytics/dwell",
    response_model=DwellAnalyticsResponse,
    tags=["analytics"],
)
def dwell_analytics(
    service: AnalyticsService = Depends(get_analytics_service),
) -> DwellAnalyticsResponse:
    return service.analytics()
