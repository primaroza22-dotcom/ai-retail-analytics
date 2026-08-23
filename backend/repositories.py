"""Data-access repositories.

Each repository owns the SQL/ORM details for one aggregate and exposes small,
intention-revealing methods. Business logic and route handlers depend on these
interfaces rather than on SQLAlchemy directly.
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .models import DwellSession, Zone, ZoneEvent


class ZoneRepository:
    """Persistence for configured zones."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, zone_id: str) -> Zone | None:
        return self._session.get(Zone, zone_id)

    def list(self) -> list[Zone]:
        return list(self._session.scalars(select(Zone).order_by(Zone.id)))

    def add(self, zone: Zone) -> Zone:
        self._session.add(zone)
        self._session.flush()
        return zone


class EventRepository:
    """Persistence for zone ENTER/EXIT events."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add_many(self, events: list[ZoneEvent]) -> None:
        self._session.add_all(events)
        self._session.flush()


class DwellRepository:
    """Persistence and aggregation for completed dwell sessions."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add_many(self, sessions: list[DwellSession]) -> None:
        self._session.add_all(sessions)
        self._session.flush()

    def list(self) -> list[DwellSession]:
        return list(
            self._session.scalars(
                select(DwellSession).order_by(DwellSession.enter_time, DwellSession.id)
            )
        )

    def summary_by_zone(self) -> list[dict]:
        """Return per-zone session count and duration aggregates."""
        rows = self._session.execute(
            select(
                DwellSession.zone_id,
                func.count(DwellSession.id),
                func.sum(DwellSession.duration),
            )
            .group_by(DwellSession.zone_id)
            .order_by(DwellSession.zone_id)
        ).all()
        result = []
        for zone_id, count, total in rows:
            count = int(count or 0)
            total = float(total or 0.0)
            result.append(
                {
                    "zone_id": zone_id,
                    "session_count": count,
                    "total_duration": total,
                    "average_duration": total / count if count else 0.0,
                }
            )
        return result
