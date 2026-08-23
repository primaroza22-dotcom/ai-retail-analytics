"""Pydantic request/response schemas for the API layer.

These are the DTOs exposed over HTTP. They are intentionally separate from the
SQLAlchemy models so the wire format can evolve independently of persistence.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ZoneCreate(BaseModel):
    id: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=256)
    polygon: list[list[float]]
    enabled: bool = True

    @field_validator("polygon")
    @classmethod
    def _polygon_has_three_points(cls, value: list[list[float]]) -> list[list[float]]:
        if len(value) < 3:
            raise ValueError("a zone polygon must have at least 3 points")
        for point in value:
            if len(point) != 2:
                raise ValueError("each polygon vertex must be an [x, y] pair")
        return value


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


class DwellSessionCreate(BaseModel):
    track_id: int = Field(ge=0)
    zone_id: str = Field(min_length=1)
    enter_time: float
    exit_time: float

    @field_validator("exit_time")
    @classmethod
    def _exit_after_enter(cls, value: float, info) -> float:
        enter = info.data.get("enter_time")
        if enter is not None and value < enter:
            raise ValueError("exit_time must be >= enter_time")
        return value


class DwellSessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    track_id: int
    zone_id: str
    enter_time: float
    exit_time: float
    duration: float


class ZoneDwellSummary(BaseModel):
    zone_id: str
    session_count: int
    total_duration: float
    average_duration: float


class DwellAnalyticsResponse(BaseModel):
    sessions: list[DwellSessionRead]
    summary: list[ZoneDwellSummary]
