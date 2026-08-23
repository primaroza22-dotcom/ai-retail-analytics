"""Database daily aggregation.

Produces ``DailyRecord`` lists from persisted zone events, dwell sessions, and
transactions. Day boundaries are computed in the configured business timezone
(DST-aware) via Python bucketing so analytics align to the business day.
"""

from __future__ import annotations

from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import STATUS_COMPLETED, DwellSession, Transaction, TransactionItem, ZoneEvent
from .records import DailyRecord
from .timezone import business_date


def aggregate_daily(
    session: Session,
    *,
    camera_id: str | None = None,
    start_time: float | None = None,
    end_time: float | None = None,
    tz: str = "UTC",
) -> list[DailyRecord]:
    buckets: dict[str, dict[str, float]] = defaultdict(
        lambda: {
            "traffic": 0.0,
            "transactions": 0.0,
            "net_sales": 0.0,
            "items_sold": 0.0,
            "dwell_count": 0.0,
            "dwell_sum": 0.0,
        }
    )

    # Traffic = zone enter events (camera-scopable visit count).
    event_clauses = [ZoneEvent.event_type == "enter"]
    if camera_id is not None:
        event_clauses.append(ZoneEvent.camera_id == camera_id)
    if start_time is not None:
        event_clauses.append(ZoneEvent.timestamp >= start_time)
    if end_time is not None:
        event_clauses.append(ZoneEvent.timestamp <= end_time)
    for (timestamp,) in session.execute(select(ZoneEvent.timestamp).where(*event_clauses)).all():
        buckets[business_date(timestamp, tz)]["traffic"] += 1.0

    # Completed dwell sessions.
    dwell_clauses = [DwellSession.status == STATUS_COMPLETED]
    if camera_id is not None:
        dwell_clauses.append(DwellSession.camera_id == camera_id)
    if start_time is not None:
        dwell_clauses.append(DwellSession.enter_time >= start_time)
    if end_time is not None:
        dwell_clauses.append(DwellSession.enter_time <= end_time)
    for enter_time, duration in session.execute(
        select(DwellSession.enter_time, DwellSession.duration).where(*dwell_clauses)
    ).all():
        date = business_date(enter_time, tz)
        buckets[date]["dwell_count"] += 1.0
        buckets[date]["dwell_sum"] += float(duration or 0.0)

    # Transactions.
    txn_clauses = []
    if start_time is not None:
        txn_clauses.append(Transaction.transaction_time >= start_time)
    if end_time is not None:
        txn_clauses.append(Transaction.transaction_time <= end_time)
    for transaction_time, total in session.execute(
        select(Transaction.transaction_time, Transaction.total).where(*txn_clauses)
    ).all():
        date = business_date(transaction_time, tz)
        buckets[date]["transactions"] += 1.0
        buckets[date]["net_sales"] += float(total or 0.0)

    for transaction_time, quantity in session.execute(
        select(Transaction.transaction_time, TransactionItem.quantity)
        .join(Transaction, TransactionItem.transaction_id == Transaction.id)
        .where(*txn_clauses)
    ).all():
        buckets[business_date(transaction_time, tz)]["items_sold"] += float(quantity or 0.0)

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
