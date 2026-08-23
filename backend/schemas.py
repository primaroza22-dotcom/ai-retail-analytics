"""Pydantic request/response schemas for the API layer.

These are the DTOs exposed over HTTP. They are intentionally separate from the
SQLAlchemy models so the wire format can evolve independently of persistence.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


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
    polygon: list[list[float]]
    enabled: bool = True

    @field_validator("polygon")
    @classmethod
    def _polygon_has_three_points(cls, value: list[list[float]]) -> list[list[float]]:
        return _validate_polygon(value)


class ZoneUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=256)
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
        if self.name is None and self.polygon is None and self.enabled is None:
            raise ValueError("at least one of name, polygon, enabled must be provided")
        return self


class ZoneRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
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
