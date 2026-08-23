"""HTTP route handlers.

Routes only translate HTTP requests into service calls and serialize results.
No business logic or database access lives here.
"""

from __future__ import annotations

import json
import time
from typing import Literal

from fastapi import APIRouter, Depends, Query, Request, WebSocket, WebSocketDisconnect, status
from fastapi.responses import JSONResponse
from sqlalchemy import text

from .deps import get_analytics_service, get_camera_service, get_transaction_service, get_zone_service
from .realtime import Event, EventType
from .schemas import (
    AnalyticsSummary,
    CameraCreate,
    CameraRead,
    CameraStatusRead,
    CameraUpdate,
    DailyAnalytics,
    DwellListResponse,
    DwellSessionCreate,
    DwellSessionRead,
    EventListResponse,
    TransactionCreate,
    TransactionDetailRead,
    TransactionItemRead,
    TransactionListResponse,
    TransactionRead,
    TransactionStatusUpdate,
    TransactionSummary,
    ZoneAnalytics,
    ZoneCreate,
    ZoneEventCreate,
    ZoneEventRead,
    ZoneRanking,
    ZoneRead,
    ZoneUpdate,
)
from .services import AnalyticsService, CameraService, TransactionService, ZoneService

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


@router.websocket("/ws/events")
async def websocket_events(websocket: WebSocket) -> None:
    """Real-time event stream with per-client camera subscription."""
    manager = websocket.app.state.connection_manager
    await manager.connect(websocket)
    await manager.send_personal(
        websocket,
        Event(EventType.CONNECTION, time.time(), {"status": "connected"}).to_dict(),
    )
    try:
        while True:
            message = await websocket.receive_text()
            _handle_subscription(manager, websocket, message)
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket)


def _handle_subscription(manager, websocket: WebSocket, message: str) -> None:
    try:
        parsed = json.loads(message)
    except json.JSONDecodeError:
        return
    if not isinstance(parsed, dict):
        return
    message_type = parsed.get("type")
    camera_ids = parsed.get("camera_ids")
    if message_type == "subscribe":
        if isinstance(camera_ids, list):
            manager.subscribe(websocket, [str(c) for c in camera_ids])
        else:
            manager.subscribe(websocket, None)
    elif message_type == "unsubscribe":
        if isinstance(camera_ids, list):
            manager.unsubscribe(websocket, [str(c) for c in camera_ids])


# --- Cameras ---


@router.post(
    "/cameras",
    response_model=CameraRead,
    status_code=status.HTTP_201_CREATED,
    tags=["cameras"],
)
def create_camera(payload: CameraCreate, camera_service=Depends(get_camera_service)) -> CameraRead:
    return camera_service.create(payload)


@router.get("/cameras", response_model=list[CameraRead], tags=["cameras"])
def list_cameras(camera_service=Depends(get_camera_service)) -> list[CameraRead]:
    return camera_service.list()


@router.get("/cameras/{camera_id}", response_model=CameraRead, tags=["cameras"])
def get_camera(camera_id: str, camera_service=Depends(get_camera_service)) -> CameraRead:
    return camera_service.get(camera_id)


@router.put("/cameras/{camera_id}", response_model=CameraRead, tags=["cameras"])
def update_camera(
    camera_id: str,
    payload: CameraUpdate,
    camera_service=Depends(get_camera_service),
) -> CameraRead:
    return camera_service.update(camera_id, payload)


@router.delete("/cameras/{camera_id}", response_model=CameraRead, tags=["cameras"])
def delete_camera(camera_id: str, camera_service=Depends(get_camera_service)) -> CameraRead:
    """Soft-delete (disable) a camera; historical references are preserved."""
    return camera_service.disable(camera_id)


@router.get("/cameras/{camera_id}/status", response_model=CameraStatusRead, tags=["cameras"])
def camera_status(
    camera_id: str,
    request: Request,
    camera_service=Depends(get_camera_service),
) -> CameraStatusRead:
    camera_service.get(camera_id)  # 404 if unknown
    status_value = request.app.state.pipeline_manager.status(camera_id).value
    return CameraStatusRead(camera_id=camera_id, status=status_value)


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
def list_zones(
    camera_id: str | None = None,
    zone_service=Depends(get_zone_service),
) -> list[ZoneRead]:
    return zone_service.list(camera_id)


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
    camera_id: str | None = None,
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
        camera_id=camera_id,
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
    camera_id: str | None = None,
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
        camera_id=camera_id,
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
    camera_id: str | None = None,
    service: AnalyticsService = Depends(get_analytics_service),
) -> AnalyticsSummary:
    return service.summary(start_time, end_time, camera_id)


@router.get("/analytics/zones", response_model=list[ZoneAnalytics], tags=["analytics"])
def zone_analytics(
    start_time: float | None = None,
    end_time: float | None = None,
    camera_id: str | None = None,
    service: AnalyticsService = Depends(get_analytics_service),
) -> list[ZoneAnalytics]:
    return service.zone_analytics(start_time, end_time, camera_id)


@router.get(
    "/analytics/zones/ranking",
    response_model=list[ZoneRanking],
    tags=["analytics"],
)
def zone_ranking(
    metric: Literal["average_dwell", "total_dwell"] = "average_dwell",
    start_time: float | None = None,
    end_time: float | None = None,
    camera_id: str | None = None,
    service: AnalyticsService = Depends(get_analytics_service),
) -> list[ZoneRanking]:
    return service.zone_ranking(metric, start_time, end_time, camera_id)


@router.get("/analytics/daily", response_model=list[DailyAnalytics], tags=["analytics"])
def daily_analytics(
    start_time: float | None = None,
    end_time: float | None = None,
    camera_id: str | None = None,
    service: AnalyticsService = Depends(get_analytics_service),
) -> list[DailyAnalytics]:
    return service.daily(start_time, end_time, camera_id)


# --- Transactions ---


@router.post(
    "/transactions/ingest",
    response_model=list[TransactionRead],
    status_code=status.HTTP_201_CREATED,
    tags=["transactions"],
)
def ingest_transactions(
    payload: list[TransactionCreate],
    service: TransactionService = Depends(get_transaction_service),
) -> list[TransactionRead]:
    """Ingest normalized POS transactions (idempotent on pos_source + external id)."""
    return service.ingest_schema(payload)


@router.get("/transactions", response_model=TransactionListResponse, tags=["transactions"])
def list_transactions(
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    start_time: float | None = None,
    end_time: float | None = None,
    status: str | None = None,
    pos_source: str | None = None,
    payment_method: str | None = None,
    terminal_id: str | None = None,
    service: TransactionService = Depends(get_transaction_service),
) -> TransactionListResponse:
    return service.list_transactions(
        limit=limit,
        offset=offset,
        start_time=start_time,
        end_time=end_time,
        status=status,
        pos_source=pos_source,
        payment_method=payment_method,
        terminal_id=terminal_id,
    )


@router.get("/transactions/summary", response_model=TransactionSummary, tags=["transactions"])
def transactions_summary(
    start_time: float | None = None,
    end_time: float | None = None,
    status: str | None = None,
    pos_source: str | None = None,
    payment_method: str | None = None,
    terminal_id: str | None = None,
    service: TransactionService = Depends(get_transaction_service),
) -> TransactionSummary:
    return service.summary(
        start_time=start_time,
        end_time=end_time,
        status=status,
        pos_source=pos_source,
        payment_method=payment_method,
        terminal_id=terminal_id,
    )


@router.get(
    "/transactions/{transaction_id}",
    response_model=TransactionDetailRead,
    tags=["transactions"],
)
def get_transaction(
    transaction_id: int,
    service: TransactionService = Depends(get_transaction_service),
) -> TransactionDetailRead:
    return service.get_transaction(transaction_id)


@router.get(
    "/transactions/{transaction_id}/items",
    response_model=list[TransactionItemRead],
    tags=["transactions"],
)
def get_transaction_items(
    transaction_id: int,
    service: TransactionService = Depends(get_transaction_service),
) -> list[TransactionItemRead]:
    return service.get_items(transaction_id)


@router.patch(
    "/transactions/{transaction_id}/status",
    response_model=TransactionRead,
    tags=["transactions"],
)
def update_transaction_status(
    transaction_id: int,
    payload: TransactionStatusUpdate,
    service: TransactionService = Depends(get_transaction_service),
) -> TransactionRead:
    return service.update_status(transaction_id, payload.status)
