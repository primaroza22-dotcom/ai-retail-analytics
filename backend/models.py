"""SQLAlchemy ORM models for persisted retail analytics.

These models mirror the analytics produced by ``ai.analytics``: zones,
zone entry/exit events, and dwell sessions. A ``track_id`` is only a temporary
identity within a tracking session and never identifies a person.

Dwell sessions can be ``ongoing`` (entered a zone, not yet exited) or
``completed``. Timestamps are Unix epoch seconds (UTC).
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base

STATUS_ONGOING = "ongoing"
STATUS_COMPLETED = "completed"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Zone(Base):
    """A configured region of interest (polygon)."""

    __tablename__ = "zones"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    polygon: Mapped[list] = mapped_column(JSON, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )

    events: Mapped[list[ZoneEvent]] = relationship(back_populates="zone")
    sessions: Mapped[list[DwellSession]] = relationship(back_populates="zone")


class ZoneEvent(Base):
    """A single ENTER or EXIT state change for a track within a zone."""

    __tablename__ = "zone_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    track_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    zone_id: Mapped[str] = mapped_column(ForeignKey("zones.id"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String, nullable=False, index=True)
    timestamp: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )

    zone: Mapped[Zone] = relationship(back_populates="events")


class DwellSession(Base):
    """A dwell session: one ENTER, optionally followed by one EXIT."""

    __tablename__ = "dwell_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    track_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    zone_id: Mapped[str] = mapped_column(ForeignKey("zones.id"), nullable=False, index=True)
    enter_time: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    exit_time: Mapped[float | None] = mapped_column(Float, nullable=True)
    duration: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(
        String, nullable=False, default=STATUS_COMPLETED, index=True
    )

    zone: Mapped[Zone] = relationship(back_populates="sessions")
