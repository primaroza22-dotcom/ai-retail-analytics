"""Business-logic services.

Services contain the domain rules (uniqueness, camera/zone existence, duration
derivation, filtering, pagination, aggregation, ranking) and delegate
persistence to repositories. Route handlers only translate HTTP into service
calls and back.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from .exceptions import ConflictError, NotFoundError
from .forecasting import (
    MIN_HISTORY,
    MODEL_NAMES,
    TARGETS,
    aggregate_daily,
    detect_anomalies,
    evaluate_candidates,
    extract_series,
    forecast_series,
    generate_insights,
    pearson,
    today_date,
    today_start_epoch,
    transaction_rate,
)
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
from .pos import NormalizedTransaction, POSAdapter
from .realtime import Event, EventBus, EventType
from .repositories import (
    CameraRepository,
    DwellRepository,
    EventRepository,
    TransactionRepository,
    ZoneRepository,
)
from .schemas import (
    AnalyticsSummary,
    CameraCreate,
    CameraRead,
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
    TransactionSummary,
    ZoneAnalytics,
    ZoneCreate,
    ZoneEventCreate,
    ZoneEventRead,
    ZoneRanking,
    ZoneRead,
    ZoneUpdate,
)


class CameraService:
    """Manages the camera registry."""

    def __init__(self, cameras: CameraRepository) -> None:
        self._cameras = cameras

    def create(self, data: CameraCreate) -> CameraRead:
        if self._cameras.get(data.id) is not None:
            raise ConflictError(f"Camera already exists: {data.id}")
        camera = Camera(
            id=data.id,
            name=data.name,
            description=data.description,
            source_type=data.source_type,
            source_url=data.source_url,
            enabled=data.enabled,
            location=data.location,
        )
        self._cameras.add(camera)
        return CameraRead.model_validate(camera)

    def list(self) -> list[CameraRead]:
        return [CameraRead.model_validate(camera) for camera in self._cameras.list()]

    def get(self, camera_id: str) -> CameraRead:
        return CameraRead.model_validate(self._require(camera_id))

    def update(self, camera_id: str, data: CameraUpdate) -> CameraRead:
        camera = self._require(camera_id)
        if data.name is not None:
            camera.name = data.name
        if data.description is not None:
            camera.description = data.description
        if data.source_type is not None:
            camera.source_type = data.source_type
        if data.source_url is not None:
            camera.source_url = data.source_url
        if data.enabled is not None:
            camera.enabled = data.enabled
        if data.location is not None:
            camera.location = data.location
        return CameraRead.model_validate(camera)

    def disable(self, camera_id: str) -> CameraRead:
        """Soft-delete a camera (preserves historical references)."""
        camera = self._require(camera_id)
        camera.enabled = False
        return CameraRead.model_validate(camera)

    def _require(self, camera_id: str) -> Camera:
        camera = self._cameras.get(camera_id)
        if camera is None:
            raise NotFoundError(f"Unknown camera: {camera_id}")
        return camera


class ZoneService:
    """Manages zone configuration."""

    def __init__(
        self,
        zones: ZoneRepository,
        cameras: CameraRepository | None = None,
    ) -> None:
        self._zones = zones
        self._cameras = cameras

    def _require_camera(self, camera_id: str | None) -> None:
        if camera_id is not None and self._cameras is not None:
            if self._cameras.get(camera_id) is None:
                raise NotFoundError(f"Unknown camera: {camera_id}")

    def create(self, data: ZoneCreate) -> ZoneRead:
        if self._zones.get(data.id) is not None:
            raise ConflictError(f"Zone already exists: {data.id}")
        self._require_camera(data.camera_id)
        zone = Zone(
            id=data.id,
            name=data.name,
            camera_id=data.camera_id,
            polygon=data.polygon,
            enabled=data.enabled,
        )
        self._zones.add(zone)
        return ZoneRead.model_validate(zone)

    def list(self, camera_id: str | None = None) -> list[ZoneRead]:
        return [ZoneRead.model_validate(zone) for zone in self._zones.list(camera_id)]

    def update(self, zone_id: str, data: ZoneUpdate) -> ZoneRead:
        zone = self._zones.get(zone_id)
        if zone is None:
            raise NotFoundError(f"Unknown zone: {zone_id}")
        if data.camera_id is not None:
            self._require_camera(data.camera_id)
            zone.camera_id = data.camera_id
        if data.name is not None:
            zone.name = data.name
        if data.polygon is not None:
            zone.polygon = data.polygon
        if data.enabled is not None:
            zone.enabled = data.enabled
        return ZoneRead.model_validate(zone)


class AnalyticsService:
    """Records events/sessions and derives dwell/occupancy aggregates."""

    def __init__(
        self,
        zones: ZoneRepository,
        events: EventRepository,
        dwell: DwellRepository,
        bus: EventBus | None = None,
    ) -> None:
        self._zones = zones
        self._events = events
        self._dwell = dwell
        self._bus = bus

    def _get_zone(self, zone_id: str) -> Zone:
        zone = self._zones.get(zone_id)
        if zone is None:
            raise NotFoundError(f"Unknown zone: {zone_id}")
        return zone

    def _publish(self, event_type: EventType, data: dict, camera_id: str | None) -> None:
        if self._bus is not None:
            self._bus.publish(Event(event_type, time.time(), data, camera_id=camera_id))

    # --- Events ---

    def record_events(self, items: list[ZoneEventCreate]) -> list[ZoneEventRead]:
        models = []
        for item in items:
            zone = self._get_zone(item.zone_id)
            models.append(
                ZoneEvent(
                    camera_id=zone.camera_id,
                    track_id=item.track_id,
                    zone_id=item.zone_id,
                    event_type=item.event_type,
                    timestamp=item.timestamp,
                )
            )
        self._events.add_many(models)
        for model in models:
            event_type = (
                EventType.ZONE_ENTER if model.event_type == "enter" else EventType.ZONE_EXIT
            )
            self._publish(
                event_type,
                {
                    "track_id": model.track_id,
                    "zone_id": model.zone_id,
                    "timestamp": model.timestamp,
                },
                model.camera_id,
            )
        return [ZoneEventRead.model_validate(model) for model in models]

    def list_events(
        self,
        *,
        limit: int,
        offset: int,
        zone_id: str | None,
        event_type: str | None,
        track_id: int | None,
        camera_id: str | None,
        start_time: float | None,
        end_time: float | None,
    ) -> EventListResponse:
        total = self._events.count(
            zone_id=zone_id,
            event_type=event_type,
            track_id=track_id,
            camera_id=camera_id,
            start_time=start_time,
            end_time=end_time,
        )
        items = [
            ZoneEventRead.model_validate(event)
            for event in self._events.list(
                limit=limit,
                offset=offset,
                zone_id=zone_id,
                event_type=event_type,
                track_id=track_id,
                camera_id=camera_id,
                start_time=start_time,
                end_time=end_time,
            )
        ]
        return EventListResponse(items=items, total=total, limit=limit, offset=offset)

    # --- Dwell sessions ---

    def record_sessions(self, items: list[DwellSessionCreate]) -> list[DwellSessionRead]:
        models = []
        for item in items:
            zone = self._get_zone(item.zone_id)
            if item.exit_time is not None:
                status = STATUS_COMPLETED
                duration = item.exit_time - item.enter_time
            else:
                status = STATUS_ONGOING
                duration = None
            models.append(
                DwellSession(
                    camera_id=zone.camera_id,
                    track_id=item.track_id,
                    zone_id=item.zone_id,
                    enter_time=item.enter_time,
                    exit_time=item.exit_time,
                    duration=duration,
                    status=status,
                )
            )
        self._dwell.add_many(models)
        for model in models:
            if model.status == STATUS_ONGOING:
                self._publish(
                    EventType.DWELL_STARTED,
                    {
                        "track_id": model.track_id,
                        "zone_id": model.zone_id,
                        "enter_time": model.enter_time,
                    },
                    model.camera_id,
                )
            else:
                self._publish(
                    EventType.DWELL_COMPLETED,
                    {
                        "track_id": model.track_id,
                        "zone_id": model.zone_id,
                        "enter_time": model.enter_time,
                        "exit_time": model.exit_time,
                        "duration": model.duration,
                    },
                    model.camera_id,
                )
        return [self._to_read(model, item.enter_time) for model, item in zip(models, items)]

    @staticmethod
    def _to_read(session: DwellSession, now: float) -> DwellSessionRead:
        if session.status == STATUS_ONGOING:
            duration = max(0.0, now - session.enter_time)
        else:
            duration = session.duration
        return DwellSessionRead(
            id=session.id,
            camera_id=session.camera_id,
            track_id=session.track_id,
            zone_id=session.zone_id,
            enter_time=session.enter_time,
            exit_time=session.exit_time,
            duration=duration,
            status=session.status,
        )

    def list_dwell_sessions(
        self,
        *,
        limit: int,
        offset: int,
        zone_id: str | None,
        track_id: int | None,
        status: str | None,
        camera_id: str | None,
        start_time: float | None,
        end_time: float | None,
        min_duration: float | None,
        max_duration: float | None,
        now: float | None,
    ) -> DwellListResponse:
        reference_now = now if now is not None else time.time()
        total = self._dwell.count(
            zone_id=zone_id,
            track_id=track_id,
            status=status,
            camera_id=camera_id,
            start_time=start_time,
            end_time=end_time,
        )
        items = [
            self._to_read(session, reference_now)
            for session in self._dwell.list(
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
            )
        ]
        return DwellListResponse(items=items, total=total, limit=limit, offset=offset)

    # --- Aggregates ---

    def summary(
        self, start_time: float | None, end_time: float | None, camera_id: str | None
    ) -> AnalyticsSummary:
        return AnalyticsSummary(**self._dwell.summary(start_time, end_time, camera_id))

    def zone_analytics(
        self, start_time: float | None, end_time: float | None, camera_id: str | None
    ) -> list[ZoneAnalytics]:
        return [
            ZoneAnalytics(**row) for row in self._dwell.by_zone(start_time, end_time, camera_id)
        ]

    def daily(
        self, start_time: float | None, end_time: float | None, camera_id: str | None
    ) -> list[DailyAnalytics]:
        result = []
        for row in self._dwell.daily(start_time, end_time, camera_id):
            date = datetime.fromtimestamp(row["day"], tz=timezone.utc).date().isoformat()
            result.append(
                DailyAnalytics(
                    date=date,
                    sessions=row["sessions"],
                    average_dwell_seconds=row["average_dwell_seconds"],
                    total_dwell_seconds=row["total_dwell_seconds"],
                )
            )
        return result

    def zone_ranking(
        self, metric: str, start_time: float | None, end_time: float | None, camera_id: str | None
    ) -> list[ZoneRanking]:
        rows = self._dwell.by_zone(start_time, end_time, camera_id)
        if metric == "total_dwell":
            key = lambda row: row["total_dwell_seconds"]  # noqa: E731
        else:
            key = lambda row: (row["average_dwell_seconds"] is not None, row["average_dwell_seconds"] or 0.0)  # noqa: E731

        ordered = sorted(rows, key=key, reverse=True)
        return [
            ZoneRanking(
                rank=index + 1,
                zone_id=row["zone_id"],
                zone_name=row["zone_name"],
                total_sessions=row["total_sessions"],
                average_dwell_seconds=row["average_dwell_seconds"],
                total_dwell_seconds=row["total_dwell_seconds"],
            )
            for index, row in enumerate(ordered)
        ]


class TransactionService:
    """Ingests, lists, and aggregates vendor-neutral POS transactions."""

    def __init__(self, transactions: TransactionRepository, bus: EventBus | None = None) -> None:
        self._transactions = transactions
        self._bus = bus

    def _publish(self, event_type: EventType, transaction: Transaction) -> None:
        if self._bus is None:
            return
        self._bus.publish(Event(event_type, time.time(), self._event_data(transaction)))

    @staticmethod
    def _event_data(transaction: Transaction) -> dict:
        return {
            "transaction_id": transaction.id,
            "external_transaction_id": transaction.external_transaction_id,
            "pos_source": transaction.pos_source,
            "store_id": transaction.store_id,
            "terminal_id": transaction.terminal_id,
            "total": transaction.total,
            "status": transaction.status,
            "payment_method": transaction.payment_method,
            "items_count": len(transaction.items),
        }

    def ingest(self, transactions: list[NormalizedTransaction]) -> list[TransactionRead]:
        results: list[TransactionRead] = []
        for normalized in transactions:
            existing = self._transactions.get_by_external(
                normalized.pos_source, normalized.external_transaction_id
            )
            if existing is not None:
                results.append(TransactionRead.model_validate(existing))
                continue
            transaction = self._build(normalized)
            self._transactions.add(transaction)
            self._publish(EventType.TRANSACTION_CREATED, transaction)
            results.append(TransactionRead.model_validate(transaction))
        return results

    def ingest_from_adapter(self, adapter: POSAdapter) -> list[TransactionRead]:
        return self.ingest(adapter.fetch_transactions())

    def ingest_schema(self, data: list[TransactionCreate]) -> list[TransactionRead]:
        return self.ingest([item.to_normalized() for item in data])

    @staticmethod
    def _build(normalized: NormalizedTransaction) -> Transaction:
        transaction = Transaction(
            external_transaction_id=normalized.external_transaction_id,
            pos_source=normalized.pos_source,
            store_id=normalized.store_id,
            terminal_id=normalized.terminal_id,
            transaction_time=normalized.transaction_time,
            subtotal=normalized.subtotal,
            discount=normalized.discount,
            tax=normalized.tax,
            total=normalized.total,
            currency=normalized.currency,
            payment_method=normalized.payment_method,
            status=normalized.status.value,
        )
        for item in normalized.items:
            line_total = (
                item.line_total
                if item.line_total is not None
                else item.quantity * item.unit_price - item.discount + item.tax
            )
            transaction.items.append(
                TransactionItem(
                    product_id=item.product_id,
                    sku=item.sku,
                    product_name=item.product_name,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    discount=item.discount,
                    tax=item.tax,
                    line_total=line_total,
                )
            )
        return transaction

    def list_transactions(
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
    ) -> TransactionListResponse:
        total = self._transactions.count(
            start_time=start_time,
            end_time=end_time,
            status=status,
            pos_source=pos_source,
            payment_method=payment_method,
            terminal_id=terminal_id,
        )
        items = [
            TransactionRead.model_validate(tx)
            for tx in self._transactions.list(
                limit=limit,
                offset=offset,
                start_time=start_time,
                end_time=end_time,
                status=status,
                pos_source=pos_source,
                payment_method=payment_method,
                terminal_id=terminal_id,
            )
        ]
        return TransactionListResponse(items=items, total=total, limit=limit, offset=offset)

    def get_transaction(self, transaction_id: int) -> TransactionDetailRead:
        transaction = self._transactions.get(transaction_id)
        if transaction is None:
            raise NotFoundError(f"Unknown transaction: {transaction_id}")
        return TransactionDetailRead(
            **TransactionRead.model_validate(transaction).model_dump(),
            items=[TransactionItemRead.model_validate(item) for item in transaction.items],
        )

    def get_items(self, transaction_id: int) -> list[TransactionItemRead]:
        transaction = self._transactions.get(transaction_id)
        if transaction is None:
            raise NotFoundError(f"Unknown transaction: {transaction_id}")
        return [
            TransactionItemRead.model_validate(item)
            for item in self._transactions.list_items(transaction_id)
        ]

    def update_status(self, transaction_id: int, new_status: str) -> TransactionRead:
        transaction = self._transactions.get(transaction_id)
        if transaction is None:
            raise NotFoundError(f"Unknown transaction: {transaction_id}")
        transaction.status = new_status
        event_type = {
            "cancelled": EventType.TRANSACTION_CANCELLED,
            "refunded": EventType.TRANSACTION_REFUNDED,
        }.get(new_status, EventType.TRANSACTION_UPDATED)
        self._publish(event_type, transaction)
        return TransactionRead.model_validate(transaction)

    def summary(
        self,
        *,
        start_time: float | None,
        end_time: float | None,
        status: str | None,
        pos_source: str | None,
        payment_method: str | None,
        terminal_id: str | None,
    ) -> TransactionSummary:
        return TransactionSummary(
            **self._transactions.summary(
                start_time=start_time,
                end_time=end_time,
                status=status,
                pos_source=pos_source,
                payment_method=payment_method,
                terminal_id=terminal_id,
            )
        )


class ForecastService:
    """Forecasting + AI analytics over daily aggregated data."""

    def __init__(
        self,
        session: Session,
        bus: EventBus | None = None,
        timezone: str = "UTC",
    ) -> None:
        self._session = session
        self._bus = bus
        self._timezone = timezone

    def _records(self, camera_id: str | None = None) -> list:
        return aggregate_daily(self._session, camera_id=camera_id, tz=self._timezone)

    @staticmethod
    def _series(records, target: str) -> tuple[list[str], list[float]]:
        series = extract_series(records, target)
        return [d for d, _ in series], [v for _, v in series]

    def forecast(self, target: str, horizon: int, camera_id: str | None = None) -> dict:
        records = self._records(camera_id)
        dates, values = self._series(records, target)
        if len(values) < MIN_HISTORY:
            return {
                "status": "insufficient_history",
                "target": target,
                "camera_id": camera_id,
                "min_history": MIN_HISTORY,
                "available": len(values),
                "forecast": [],
                "evaluation": [],
            }
        result = forecast_series(dates, values, horizon)
        return {
            "status": "ok",
            "target": target,
            "horizon": horizon,
            "camera_id": camera_id,
            "model": result["model"],
            "forecast": result["points"],
            "evaluation": result["evaluation"],
        }

    def evaluation(self, target: str, camera_id: str | None = None) -> dict:
        records = self._records(camera_id)
        dates, values = self._series(records, target)
        if len(values) < MIN_HISTORY:
            return {
                "status": "insufficient_history",
                "target": target,
                "min_history": MIN_HISTORY,
                "available": len(values),
                "results": [],
            }
        return {
            "status": "ok",
            "target": target,
            "camera_id": camera_id,
            "results": evaluate_candidates(dates, values),
        }

    @staticmethod
    def models() -> dict:
        return {"models": [{"name": name, "version": "1"} for name in MODEL_NAMES]}

    def trends(self, camera_id: str | None = None) -> list[dict]:
        records = self._records(camera_id)
        ordered = sorted(records, key=lambda r: r.date)
        if len(ordered) < 14:
            return []
        trends = []
        for target in TARGETS:
            values = [record.value(target) for record in ordered]
            recent = sum(values[-7:]) / 7
            previous = sum(values[-14:-7]) / 7
            if previous == 0:
                continue
            change = (recent - previous) / abs(previous)
            trends.append(
                {
                    "target": target,
                    "recent_avg": recent,
                    "previous_avg": previous,
                    "change_pct": round(change * 100, 2),
                }
            )
        return trends

    def correlations(self, camera_id: str | None = None) -> list[dict]:
        records = sorted(self._records(camera_id), key=lambda r: r.date)
        if len(records) < 2:
            return []

        def series(metric: str) -> list[float]:
            if metric == "avg_dwell":
                return [r.avg_dwell if r.avg_dwell is not None else 0.0 for r in records]
            return [r.value(metric) for r in records]

        pairs = [
            ("traffic", "transactions"),
            ("traffic", "net_sales"),
            ("avg_dwell", "transactions"),
            ("transactions", "net_sales"),
        ]
        results = []
        for a, b in pairs:
            value = pearson(series(a), series(b))
            if value is not None:
                results.append({"a": a, "b": b, "correlation": round(value, 4)})
        return results

    def anomalies(self, camera_id: str | None = None) -> list[dict]:
        records = sorted(self._records(camera_id), key=lambda r: r.date)
        anomalies = []
        for target in ("traffic", "transactions", "net_sales"):
            dates = [r.date for r in records]
            values = [r.value(target) for r in records]
            for anomaly in detect_anomalies(dates, values):
                anomalies.append({**anomaly, "metric": target})
        anomalies.sort(key=lambda a: a["date"], reverse=True)
        return anomalies

    def insights(self, camera_id: str | None = None) -> list[dict]:
        return generate_insights(self._records(camera_id))

    def today(self) -> dict:
        start = today_start_epoch(self._timezone)
        records = aggregate_daily(self._session, start_time=start, tz=self._timezone)
        record = records[0] if records else None
        return {
            "date": today_date(self._timezone),
            "transactions": int(record.transactions) if record else 0,
            "net_sales": float(record.net_sales) if record else 0.0,
            "items_sold": float(record.items_sold) if record else 0.0,
            "traffic": float(record.traffic) if record else 0.0,
            "avg_transaction_value": record.avg_transaction_value if record else None,
        }

    def refresh(self) -> dict:
        """Recompute forecasts/insights/anomalies and publish real-time events."""
        published = {"forecast_updated": 0, "analytics_insight": 0, "anomaly_detected": 0}

        for target in ("traffic", "transactions", "net_sales"):
            result = self.forecast(target, horizon=7)
            if result["status"] != "ok":
                continue
            self._publish(
                EventType.FORECAST_UPDATED,
                {
                    "target": target,
                    "horizon": 7,
                    "model": result["model"],
                    "forecast": result["forecast"],
                },
            )
            published["forecast_updated"] += 1

        for insight in self.insights():
            self._publish(EventType.ANALYTICS_INSIGHT, insight)
            published["analytics_insight"] += 1

        for anomaly in self.anomalies():
            self._publish(EventType.ANOMALY_DETECTED, anomaly)
            published["anomaly_detected"] += 1

        return {"published": published}

    def _publish(self, event_type: EventType, data: dict) -> None:
        if self._bus is not None:
            self._bus.publish(Event(event_type, time.time(), data))
