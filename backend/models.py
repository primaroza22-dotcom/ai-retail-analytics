"""SQLAlchemy ORM models for persisted retail analytics.

These models mirror the analytics produced by ``ai.analytics``: cameras, zones,
zone entry/exit events, and dwell sessions. A ``track_id`` is only a temporary
identity within a single camera's tracking session and never identifies a
person. Track identity is camera-scoped: ``(camera_id, track_id)``.

Dwell sessions can be ``ongoing`` (entered a zone, not yet exited) or
``completed``. Timestamps are Unix epoch seconds (UTC).
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base

STATUS_ONGOING = "ongoing"
STATUS_COMPLETED = "completed"

SOURCE_TYPES = ("rtsp", "onvif", "file", "test")

TRANSACTION_STATUSES = ("pending", "completed", "cancelled", "refunded")
STATUS_PENDING = "pending"
STATUS_CANCELLED = "cancelled"
STATUS_REFUNDED = "refunded"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Camera(Base):
    """A registered camera (input source) for one pipeline."""

    __tablename__ = "cameras"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    source_type: Mapped[str] = mapped_column(String, nullable=False, default="rtsp")
    source_url: Mapped[str | None] = mapped_column(String, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    location: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )

    zones: Mapped[list[Zone]] = relationship(back_populates="camera")


class Zone(Base):
    """A configured region of interest (polygon), scoped to one camera."""

    __tablename__ = "zones"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    camera_id: Mapped[str | None] = mapped_column(
        ForeignKey("cameras.id"), nullable=True, index=True
    )
    polygon: Mapped[list] = mapped_column(JSON, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )

    camera: Mapped[Camera | None] = relationship(back_populates="zones")
    events: Mapped[list[ZoneEvent]] = relationship(back_populates="zone")
    sessions: Mapped[list[DwellSession]] = relationship(back_populates="zone")


class ZoneEvent(Base):
    """A single ENTER or EXIT state change for a track within a zone."""

    __tablename__ = "zone_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    camera_id: Mapped[str | None] = mapped_column(
        ForeignKey("cameras.id"), nullable=True, index=True
    )
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
    camera_id: Mapped[str | None] = mapped_column(
        ForeignKey("cameras.id"), nullable=True, index=True
    )
    track_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    zone_id: Mapped[str] = mapped_column(ForeignKey("zones.id"), nullable=False, index=True)
    enter_time: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    exit_time: Mapped[float | None] = mapped_column(Float, nullable=True)
    duration: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(
        String, nullable=False, default=STATUS_COMPLETED, index=True
    )

    zone: Mapped[Zone] = relationship(back_populates="sessions")


class Transaction(Base):
    """A vendor-neutral POS transaction."""

    __tablename__ = "transactions"
    __table_args__ = (
        UniqueConstraint("pos_source", "external_transaction_id", name="uq_transactions_pos_external"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    external_transaction_id: Mapped[str] = mapped_column(String, nullable=False)
    pos_source: Mapped[str] = mapped_column(String, nullable=False, index=True)
    store_id: Mapped[str | None] = mapped_column(String, nullable=True)
    terminal_id: Mapped[str | None] = mapped_column(String, nullable=True)
    transaction_time: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    subtotal: Mapped[float] = mapped_column(Float, nullable=False)
    discount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    tax: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    total: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String, nullable=False, default="USD")
    payment_method: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default=STATUS_COMPLETED, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )

    items: Mapped[list[TransactionItem]] = relationship(
        back_populates="transaction", cascade="all, delete-orphan"
    )


class TransactionItem(Base):
    """A single line item of a POS transaction."""

    __tablename__ = "transaction_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    transaction_id: Mapped[int] = mapped_column(
        ForeignKey("transactions.id"), nullable=False, index=True
    )
    product_id: Mapped[str | None] = mapped_column(String, nullable=True)
    sku: Mapped[str | None] = mapped_column(String, nullable=True)
    product_name: Mapped[str | None] = mapped_column(String, nullable=True)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    unit_price: Mapped[float] = mapped_column(Float, nullable=False)
    discount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    tax: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    line_total: Mapped[float] = mapped_column(Float, nullable=False)

    transaction: Mapped[Transaction] = relationship(back_populates="items")
