"""Pydantic request/response schemas for the API layer.

These are the DTOs exposed over HTTP. They are intentionally separate from the
SQLAlchemy models so the wire format can evolve independently of persistence.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .models import TRANSACTION_STATUSES
from .pos.models import NormalizedItem, NormalizedTransaction, TransactionStatus

SOURCE_TYPES = {"rtsp", "onvif", "file", "test"}


def _validate_polygon(value: list[list[float]]) -> list[list[float]]:
    if len(value) < 3:
        raise ValueError("a zone polygon must have at least 3 points")
    for point in value:
        if len(point) != 2:
            raise ValueError("each polygon vertex must be an [x, y] pair")
        if any(not isinstance(coord, (int, float)) for coord in point):
            raise ValueError("polygon coordinates must be numbers")
    return value


class ZoneCreate(BaseModel):
    id: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=256)
    camera_id: str | None = None
    polygon: list[list[float]]
    enabled: bool = True

    @field_validator("polygon")
    @classmethod
    def _polygon_has_three_points(cls, value: list[list[float]]) -> list[list[float]]:
        return _validate_polygon(value)


class ZoneUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=256)
    camera_id: str | None = None
    polygon: list[list[float]] | None = None
    enabled: bool | None = None

    @field_validator("polygon")
    @classmethod
    def _polygon_valid_when_present(cls, value: list[list[float]] | None) -> list[list[float]] | None:
        if value is None:
            return value
        return _validate_polygon(value)

    @model_validator(mode="after")
    def _at_least_one_field(self) -> ZoneUpdate:
        if (
            self.name is None
            and self.polygon is None
            and self.enabled is None
            and self.camera_id is None
        ):
            raise ValueError("at least one of name, polygon, enabled, camera_id must be provided")
        return self


class ZoneRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    camera_id: str | None
    polygon: list[list[float]]
    enabled: bool
    created_at: datetime


class ZoneEventCreate(BaseModel):
    track_id: int = Field(ge=0)
    zone_id: str = Field(min_length=1)
    event_type: str = Field(pattern="^(enter|exit)$")
    timestamp: float


class ZoneEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    camera_id: str | None
    track_id: int
    zone_id: str
    event_type: str
    timestamp: float
    created_at: datetime


class EventListResponse(BaseModel):
    items: list[ZoneEventRead]
    total: int
    limit: int
    offset: int


class DwellSessionCreate(BaseModel):
    track_id: int = Field(ge=0)
    zone_id: str = Field(min_length=1)
    enter_time: float
    exit_time: float | None = None

    @field_validator("exit_time")
    @classmethod
    def _exit_after_enter(cls, value: float | None, info) -> float | None:
        enter = info.data.get("enter_time")
        if value is not None and enter is not None and value < enter:
            raise ValueError("exit_time must be >= enter_time")
        return value


class DwellSessionRead(BaseModel):
    id: int
    camera_id: str | None
    track_id: int
    zone_id: str
    enter_time: float
    exit_time: float | None
    duration: float | None
    status: str


class DwellListResponse(BaseModel):
    items: list[DwellSessionRead]
    total: int
    limit: int
    offset: int


class AnalyticsSummary(BaseModel):
    total_sessions: int
    completed_sessions: int
    ongoing_sessions: int
    average_dwell_seconds: float | None
    max_dwell_seconds: float | None
    min_dwell_seconds: float | None


class ZoneAnalytics(BaseModel):
    zone_id: str
    zone_name: str
    total_sessions: int
    completed_sessions: int
    ongoing_sessions: int
    average_dwell_seconds: float | None
    total_dwell_seconds: float
    max_dwell_seconds: float | None


class DailyAnalytics(BaseModel):
    date: str
    sessions: int
    average_dwell_seconds: float | None
    total_dwell_seconds: float


class ZoneRanking(BaseModel):
    rank: int
    zone_id: str
    zone_name: str
    total_sessions: int
    average_dwell_seconds: float | None
    total_dwell_seconds: float


class CameraCreate(BaseModel):
    id: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=256)
    description: str | None = None
    source_type: str = "rtsp"
    source_url: str | None = None
    enabled: bool = True
    location: str | None = None

    @field_validator("source_type")
    @classmethod
    def _valid_source_type(cls, value: str) -> str:
        if value not in SOURCE_TYPES:
            raise ValueError(f"source_type must be one of {sorted(SOURCE_TYPES)}")
        return value


class CameraUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=256)
    description: str | None = None
    source_type: str | None = None
    source_url: str | None = None
    enabled: bool | None = None
    location: str | None = None

    @field_validator("source_type")
    @classmethod
    def _valid_source_type(cls, value: str | None) -> str | None:
        if value is not None and value not in SOURCE_TYPES:
            raise ValueError(f"source_type must be one of {sorted(SOURCE_TYPES)}")
        return value


class CameraRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None
    source_type: str
    source_url: str | None
    enabled: bool
    location: str | None
    created_at: datetime
    updated_at: datetime


class CameraStatusRead(BaseModel):
    camera_id: str
    status: str


class TransactionItemCreate(BaseModel):
    product_id: str | None = None
    sku: str | None = None
    product_name: str | None = None
    quantity: float = Field(gt=0)
    unit_price: float = Field(ge=0)
    discount: float = Field(default=0, ge=0)
    tax: float = Field(default=0, ge=0)
    line_total: float | None = None


class TransactionCreate(BaseModel):
    external_transaction_id: str = Field(min_length=1)
    pos_source: str = Field(min_length=1)
    store_id: str | None = None
    terminal_id: str | None = None
    transaction_time: float
    subtotal: float = Field(ge=0)
    discount: float = Field(default=0, ge=0)
    tax: float = Field(default=0, ge=0)
    total: float = Field(ge=0)
    currency: str = "USD"
    payment_method: str | None = None
    status: str = "completed"
    items: list[TransactionItemCreate] = []

    @field_validator("status")
    @classmethod
    def _valid_status(cls, value: str) -> str:
        if value not in TRANSACTION_STATUSES:
            raise ValueError(f"status must be one of {TRANSACTION_STATUSES}")
        return value

    def to_normalized(self) -> NormalizedTransaction:
        return NormalizedTransaction(
            external_transaction_id=self.external_transaction_id,
            pos_source=self.pos_source,
            store_id=self.store_id,
            terminal_id=self.terminal_id,
            transaction_time=self.transaction_time,
            subtotal=self.subtotal,
            discount=self.discount,
            tax=self.tax,
            total=self.total,
            currency=self.currency,
            payment_method=self.payment_method,
            status=TransactionStatus(self.status),
            items=[
                NormalizedItem(
                    product_id=item.product_id,
                    sku=item.sku,
                    product_name=item.product_name,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    discount=item.discount,
                    tax=item.tax,
                    line_total=item.line_total,
                )
                for item in self.items
            ],
        )


class TransactionItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: str | None
    sku: str | None
    product_name: str | None
    quantity: float
    unit_price: float
    discount: float
    tax: float
    line_total: float


class TransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    external_transaction_id: str
    pos_source: str
    store_id: str | None
    terminal_id: str | None
    transaction_time: float
    subtotal: float
    discount: float
    tax: float
    total: float
    currency: str
    payment_method: str | None
    status: str
    created_at: datetime
    updated_at: datetime


class TransactionDetailRead(TransactionRead):
    items: list[TransactionItemRead]


class TransactionListResponse(BaseModel):
    items: list[TransactionRead]
    total: int
    limit: int
    offset: int


class TransactionStatusUpdate(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def _valid_status(cls, value: str) -> str:
        if value not in TRANSACTION_STATUSES:
            raise ValueError(f"status must be one of {TRANSACTION_STATUSES}")
        return value


class PaymentMethodBreakdown(BaseModel):
    payment_method: str | None
    count: int
    total: float


class TransactionSummary(BaseModel):
    transaction_count: int
    gross_sales: float
    discount_total: float
    tax_total: float
    net_sales: float
    average_transaction_value: float | None
    items_sold: float
    by_payment_method: list[PaymentMethodBreakdown]
