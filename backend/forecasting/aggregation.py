"""Database daily aggregation.

Produces ``DailyRecord`` lists from persisted zone events, dwell sessions, and
transactions. Aggregation is grouped by UTC day in SQL and converted to the
configured business timezone (exact for UTC; approximate for other timezones,
which is acceptable at a daily grain for this foundation sprint).
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import STATUS_COMPLETED, DwellSession, Transaction, TransactionItem, ZoneEvent
from .records import DailyRecord

_DAY_SECONDS = 86400


def _business_date(day_start_ts: float, tz: str) -> str:
    if tz == "UTC":
        return datetime.fromtimestamp(day_start_ts, tz=timezone.utc).date().isoformat()
    return datetime.fromtimestamp(day_start_ts, tz=ZoneInfo(tz)).date().isoformat()


def _day_key(column):
    # Day-start epoch timestamp (UTC midnight) for the given timestamp column.
    return column - (column % _DAY_SECONDS)


def aggregate_daily(
    session: Session,
    *,
    camera_id: str | None = None,
    start_time: float | None = None,
    end_time: float | None = None,
    tz: str = "UTC",
) -> list[DailyRecord]:
    buckets: dict[str, dict[str, float]] = defaultdict(
        lambda: {"traffic": 0.0, "transactions": 0.0, "net_sales": 0.0, "items_sold": 0.0, "dwell_count": 0.0, "dwell_sum": 0.0}
    )

    # Traffic = zone enter events.
    event_clauses = [ZoneEvent.event_type == "enter"]
    if camera_id is not None:
        event_clauses.append(ZoneEvent.camera_id == camera_id)
    if start_time is not None:
        event_clauses.append(ZoneEvent.timestamp >= start_time)
    if end_time is not None:
        event_clauses.append(ZoneEvent.timestamp <= end_time)
    for day, count in session.execute(
        select(_day_key(ZoneEvent.timestamp), func.count(ZoneEvent.id))
        .where(*event_clauses)
        .group_by(_day_key(ZoneEvent.timestamp))
    ).all():
        buckets[_business_date(float(day), tz)]["traffic"] += float(count or 0)

    # Completed dwell sessions.
    dwell_clauses = [DwellSession.status == STATUS_COMPLETED]
    if camera_id is not None:
        dwell_clauses.append(DwellSession.camera_id == camera_id)
    if start_time is not None:
        dwell_clauses.append(DwellSession.enter_time >= start_time)
    if end_time is not None:
        dwell_clauses.append(DwellSession.enter_time <= end_time)
    for day, count, total in session.execute(
        select(_day_key(DwellSession.enter_time), func.count(DwellSession.id), func.sum(DwellSession.duration))
        .where(*dwell_clauses)
        .group_by(_day_key(DwellSession.enter_time))
    ).all():
        buckets[_business_date(float(day), tz)]["dwell_count"] += float(count or 0)
        buckets[_business_date(float(day), tz)]["dwell_sum"] += float(total or 0.0)

    # Transactions.
    txn_clauses = []
    if start_time is not None:
        txn_clauses.append(Transaction.transaction_time >= start_time)
    if end_time is not None:
        txn_clauses.append(Transaction.transaction_time <= end_time)
    for day, count, total in session.execute(
        select(_day_key(Transaction.transaction_time), func.count(Transaction.id), func.sum(Transaction.total))
        .where(*txn_clauses)
        .group_by(_day_key(Transaction.transaction_time))
    ).all():
        buckets[_business_date(float(day), tz)]["transactions"] += float(count or 0)
        buckets[_business_date(float(day), tz)]["net_sales"] += float(total or 0.0)

    for day, total in session.execute(
        select(_day_key(Transaction.transaction_time), func.sum(TransactionItem.quantity))
        .join(Transaction, TransactionItem.transaction_id == Transaction.id)
        .where(*txn_clauses)
        .group_by(_day_key(Transaction.transaction_time))
    ).all():
        buckets[_business_date(float(day), tz)]["items_sold"] += float(total or 0.0)

    records = []
    for date in sorted(buckets):
        bucket = buckets[date]
        transactions = bucket["transactions"]
        net_sales = bucket["net_sales"]
        dwell_count = bucket["dwell_count"]
        records.append(
            DailyRecord(
                date=date,
                traffic=bucket["traffic"],
                transactions=transactions,
                net_sales=net_sales,
                items_sold=bucket["items_sold"],
                avg_transaction_value=(net_sales / transactions) if transactions else None,
                avg_dwell=(bucket["dwell_sum"] / dwell_count) if dwell_count else None,
            )
        )
    return records
