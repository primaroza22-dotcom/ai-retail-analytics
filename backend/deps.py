"""FastAPI dependency providers.

A single SQLAlchemy session is opened per request and committed on success or
rolled back on error. Services are built from repositories bound to that
session, keeping database access out of the route handlers.
"""

from __future__ import annotations

from collections.abc import Iterator

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from .repositories import (
    CameraRepository,
    DwellRepository,
    EventRepository,
    TransactionRepository,
    ZoneRepository,
)
from .services import AnalyticsService, CameraService, TransactionService, ZoneService


def get_session(request: Request) -> Iterator[Session]:
    factory = request.app.state.session_factory
    session: Session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_zone_service(session: Session = Depends(get_session)) -> ZoneService:
    return ZoneService(ZoneRepository(session), CameraRepository(session))


def get_camera_service(session: Session = Depends(get_session)) -> CameraService:
    return CameraService(CameraRepository(session))


def get_analytics_service(request: Request, session: Session = Depends(get_session)) -> AnalyticsService:
    return AnalyticsService(
        ZoneRepository(session),
        EventRepository(session),
        DwellRepository(session),
        bus=request.app.state.event_bus,
    )


def get_transaction_service(request: Request, session: Session = Depends(get_session)) -> TransactionService:
    return TransactionService(
        TransactionRepository(session),
        bus=request.app.state.event_bus,
    )
