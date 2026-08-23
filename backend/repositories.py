"""Data-access repositories.

Each repository owns the SQL/ORM details for one aggregate and exposes small,
intention-revealing methods. Business logic and route handlers depend on these
interfaces rather than on SQLAlchemy directly. Aggregations (COUNT/AVG/SUM/
MAX/MIN) are performed database-side.
"""

from __future__ import annotations

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from .models import (
    STATUS_COMPLETED,
    STATUS_ONGOING,
    Camera,
    DwellSession,
    Transaction,
    TransactionItem,
    Zone,
    ZoneEvent,
)

_DAY_SECONDS = 86400


class CameraRepository:
    """Persistence for registered cameras."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, camera_id: str) -> Camera | None:
        return self._session.get(Camera, camera_id)

    def list(self) -> list[Camera]:
        return list(self._session.scalars(select(Camera).order_by(Camera.id)))

    def add(self, camera: Camera) -> Camera:
        self._session.add(camera)
        self._session.flush()
        return camera


class ZoneRepository:
    """Persistence for configured zones."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, zone_id: str) -> Zone | None:
        return self._session.get(Zone, zone_id)

    def list(self, camera_id: str | None = None) -> list[Zone]:
        stmt = select(Zone).order_by(Zone.id)
        if camera_id is not None:
            stmt = stmt.where(Zone.camera_id == camera_id)
        return list(self._session.scalars(stmt))

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

    @staticmethod
    def _filters(
        zone_id: str | None,
        event_type: str | None,
        track_id: int | None,
        camera_id: str | None,
        start_time: float | None,
        end_time: float | None,
    ) -> list:
        clauses = []
        if zone_id is not None:
            clauses.append(ZoneEvent.zone_id == zone_id)
        if event_type is not None:
            clauses.append(ZoneEvent.event_type == event_type)
        if track_id is not None:
            clauses.append(ZoneEvent.track_id == track_id)
        if camera_id is not None:
            clauses.append(ZoneEvent.camera_id == camera_id)
        if start_time is not None:
            clauses.append(ZoneEvent.timestamp >= start_time)
        if end_time is not None:
            clauses.append(ZoneEvent.timestamp <= end_time)
        return clauses

    def list(
        self,
        *,
        limit: int,
        offset: int,
        zone_id: str | None = None,
        event_type: str | None = None,
        track_id: int | None = None,
        camera_id: str | None = None,
        start_time: float | None = None,
        end_time: float | None = None,
    ) -> list[ZoneEvent]:
        stmt = select(ZoneEvent).where(
            *self._filters(zone_id, event_type, track_id, camera_id, start_time, end_time)
        )
        stmt = stmt.order_by(ZoneEvent.id).limit(limit).offset(offset)
        return list(self._session.scalars(stmt))

    def count(
        self,
        *,
        zone_id: str | None = None,
        event_type: str | None = None,
        track_id: int | None = None,
        camera_id: str | None = None,
        start_time: float | None = None,
        end_time: float | None = None,
    ) -> int:
        stmt = select(func.count(ZoneEvent.id)).where(
            *self._filters(zone_id, event_type, track_id, camera_id, start_time, end_time)
        )
        return int(self._session.scalar(stmt) or 0)


class DwellRepository:
    """Persistence and database-side aggregation for dwell sessions."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add_many(self, sessions: list[DwellSession]) -> None:
        self._session.add_all(sessions)
        self._session.flush()

    @staticmethod
    def _filters(
        zone_id: str | None,
        track_id: int | None,
        status: str | None,
        camera_id: str | None,
        start_time: float | None,
        end_time: float | None,
        min_duration: float | None,
        max_duration: float | None,
    ) -> list:
        clauses = []
        if zone_id is not None:
            clauses.append(DwellSession.zone_id == zone_id)
        if track_id is not None:
            clauses.append(DwellSession.track_id == track_id)
        if status is not None:
            clauses.append(DwellSession.status == status)
        if camera_id is not None:
            clauses.append(DwellSession.camera_id == camera_id)
        if start_time is not None:
            clauses.append(DwellSession.enter_time >= start_time)
        if end_time is not None:
            clauses.append(DwellSession.enter_time <= end_time)
        if min_duration is not None:
            clauses.append(DwellSession.duration >= min_duration)
        if max_duration is not None:
            clauses.append(DwellSession.duration <= max_duration)
        return clauses

    def list(
        self,
        *,
        limit: int,
        offset: int,
        zone_id: str | None = None,
        track_id: int | None = None,
        status: str | None = None,
        camera_id: str | None = None,
        start_time: float | None = None,
        end_time: float | None = None,
        min_duration: float | None = None,
        max_duration: float | None = None,
    ) -> list[DwellSession]:
        stmt = select(DwellSession).where(
            *self._filters(
                zone_id, track_id, status, camera_id, start_time, end_time, min_duration, max_duration
            )
        )
        stmt = stmt.order_by(DwellSession.enter_time, DwellSession.id).limit(limit).offset(offset)
        return list(self._session.scalars(stmt))

    def count(
        self,
        *,
        zone_id: str | None = None,
        track_id: int | None = None,
        status: str | None = None,
        camera_id: str | None = None,
        start_time: float | None = None,
        end_time: float | None = None,
    ) -> int:
        stmt = select(func.count(DwellSession.id)).where(
            *self._filters(zone_id, track_id, status, camera_id, start_time, end_time, None, None)
        )
        return int(self._session.scalar(stmt) or 0)

    @staticmethod
    def _time_filters(start_time: float | None, end_time: float | None) -> list:
        clauses = []
        if start_time is not None:
            clauses.append(DwellSession.enter_time >= start_time)
        if end_time is not None:
            clauses.append(DwellSession.enter_time <= end_time)
        return clauses

    def summary(
        self, start_time: float | None, end_time: float | None, camera_id: str | None
    ) -> dict:
        completed = case((DwellSession.status == STATUS_COMPLETED, DwellSession.duration))
        is_completed = case((DwellSession.status == STATUS_COMPLETED, 1), else_=0)
        is_ongoing = case((DwellSession.status == STATUS_ONGOING, 1), else_=0)
        clauses = self._time_filters(start_time, end_time)
        if camera_id is not None:
            clauses.append(DwellSession.camera_id == camera_id)
        row = self._session.execute(
            select(
                func.count(DwellSession.id),
                func.sum(is_completed),
                func.sum(is_ongoing),
                func.avg(completed),
                func.max(completed),
                func.min(completed),
            ).where(*clauses)
        ).one()
        return {
            "total_sessions": int(row[0] or 0),
            "completed_sessions": int(row[1] or 0),
            "ongoing_sessions": int(row[2] or 0),
            "average_dwell_seconds": self._as_float(row[3]),
            "max_dwell_seconds": self._as_float(row[4]),
            "min_dwell_seconds": self._as_float(row[5]),
        }

    def by_zone(
        self, start_time: float | None, end_time: float | None, camera_id: str | None
    ) -> list[dict]:
        completed = case((DwellSession.status == STATUS_COMPLETED, DwellSession.duration))
        is_completed = case((DwellSession.status == STATUS_COMPLETED, 1), else_=0)
        is_ongoing = case((DwellSession.status == STATUS_ONGOING, 1), else_=0)
        clauses = self._time_filters(start_time, end_time)
        if camera_id is not None:
            clauses.append(DwellSession.camera_id == camera_id)
        rows = self._session.execute(
            select(
                DwellSession.zone_id,
                Zone.name,
                func.count(DwellSession.id),
                func.sum(is_completed),
                func.sum(is_ongoing),
                func.avg(completed),
                func.sum(completed),
                func.max(completed),
            )
            .join(Zone, DwellSession.zone_id == Zone.id)
            .where(*clauses)
            .group_by(DwellSession.zone_id, Zone.name)
            .order_by(DwellSession.zone_id)
        ).all()
        return [
            {
                "zone_id": row[0],
                "zone_name": row[1],
                "total_sessions": int(row[2] or 0),
                "completed_sessions": int(row[3] or 0),
                "ongoing_sessions": int(row[4] or 0),
                "average_dwell_seconds": self._as_float(row[5]),
                "total_dwell_seconds": float(row[6] or 0.0),
                "max_dwell_seconds": self._as_float(row[7]),
            }
            for row in rows
        ]

    def daily(
        self, start_time: float | None, end_time: float | None, camera_id: str | None
    ) -> list[dict]:
        completed = case((DwellSession.status == STATUS_COMPLETED, DwellSession.duration))
        day_start = DwellSession.enter_time - (DwellSession.enter_time % _DAY_SECONDS)
        clauses = [DwellSession.status == STATUS_COMPLETED]
        clauses.extend(self._time_filters(start_time, end_time))
        if camera_id is not None:
            clauses.append(DwellSession.camera_id == camera_id)
        rows = self._session.execute(
            select(
                day_start.label("day"),
                func.count(DwellSession.id),
                func.avg(completed),
                func.sum(completed),
            )
            .where(*clauses)
            .group_by("day")
            .order_by("day")
        ).all()
        return [
            {
                "day": float(row[0]),
                "sessions": int(row[1] or 0),
                "average_dwell_seconds": self._as_float(row[2]),
                "total_dwell_seconds": float(row[3] or 0.0),
            }
            for row in rows
        ]

    @staticmethod
    def _as_float(value) -> float | None:
        return float(value) if value is not None else None


class TransactionRepository:
    """Persistence and database-side aggregation for POS transactions."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, transaction_id: int) -> Transaction | None:
        return self._session.get(Transaction, transaction_id)

    def get_by_external(self, pos_source: str, external_transaction_id: str) -> Transaction | None:
        return self._session.scalar(
            select(Transaction).where(
                Transaction.pos_source == pos_source,
                Transaction.external_transaction_id == external_transaction_id,
            )
        )

    def add(self, transaction: Transaction) -> Transaction:
        self._session.add(transaction)
        self._session.flush()
        return transaction

    @staticmethod
    def _filters(
        start_time: float | None,
        end_time: float | None,
        status: str | None,
        pos_source: str | None,
        payment_method: str | None,
        terminal_id: str | None,
    ) -> list:
        clauses = []
        if start_time is not None:
            clauses.append(Transaction.transaction_time >= start_time)
        if end_time is not None:
            clauses.append(Transaction.transaction_time <= end_time)
        if status is not None:
            clauses.append(Transaction.status == status)
        if pos_source is not None:
            clauses.append(Transaction.pos_source == pos_source)
        if payment_method is not None:
            clauses.append(Transaction.payment_method == payment_method)
        if terminal_id is not None:
            clauses.append(Transaction.terminal_id == terminal_id)
        return clauses

    def list(
        self,
        *,
        limit: int,
        offset: int,
        start_time: float | None,
        end_time: float | None,
        status: str | None,
        pos_source: str | None,
        payment_method: str | None,
        terminal_id: str | None,
    ) -> list[Transaction]:
        stmt = select(Transaction).where(
            *self._filters(start_time, end_time, status, pos_source, payment_method, terminal_id)
        )
        stmt = stmt.order_by(Transaction.id.desc()).limit(limit).offset(offset)
        return list(self._session.scalars(stmt))

    def count(
        self,
        *,
        start_time: float | None,
        end_time: float | None,
        status: str | None,
        pos_source: str | None,
        payment_method: str | None,
        terminal_id: str | None,
    ) -> int:
        stmt = select(func.count(Transaction.id)).where(
            *self._filters(start_time, end_time, status, pos_source, payment_method, terminal_id)
        )
        return int(self._session.scalar(stmt) or 0)

    def list_items(self, transaction_id: int) -> list[TransactionItem]:
        return list(
            self._session.scalars(
                select(TransactionItem)
                .where(TransactionItem.transaction_id == transaction_id)
                .order_by(TransactionItem.id)
            )
        )

    def summary(
        self,
        *,
        start_time: float | None,
        end_time: float | None,
        status: str | None,
        pos_source: str | None,
        payment_method: str | None,
        terminal_id: str | None,
    ) -> dict:
        filters = self._filters(start_time, end_time, status, pos_source, payment_method, terminal_id)

        row = self._session.execute(
            select(
                func.count(Transaction.id),
                func.sum(Transaction.subtotal),
                func.sum(Transaction.discount),
                func.sum(Transaction.tax),
                func.sum(Transaction.total),
                func.avg(Transaction.total),
            ).where(*filters)
        ).one()

        items_sold = self._session.scalar(
            select(func.coalesce(func.sum(TransactionItem.quantity), 0.0))
            .join(Transaction, TransactionItem.transaction_id == Transaction.id)
            .where(*filters)
        ) or 0.0

        pm_rows = self._session.execute(
            select(
                Transaction.payment_method,
                func.count(Transaction.id),
                func.sum(Transaction.total),
            )
            .where(*filters)
            .group_by(Transaction.payment_method)
            .order_by(Transaction.payment_method)
        ).all()

        return {
            "transaction_count": int(row[0] or 0),
            "gross_sales": float(row[1] or 0.0),
            "discount_total": float(row[2] or 0.0),
            "tax_total": float(row[3] or 0.0),
            "net_sales": float(row[4] or 0.0),
            "average_transaction_value": self._as_float(row[5]),
            "items_sold": float(items_sold),
            "by_payment_method": [
                {
                    "payment_method": r[0],
                    "count": int(r[1] or 0),
                    "total": float(r[2] or 0.0),
                }
                for r in pm_rows
            ],
        }

    @staticmethod
    def _as_float(value) -> float | None:
        return float(value) if value is not None else None
