"""Timezone helpers for analytics.

All timestamps are stored as Unix epoch seconds (UTC). Daily aggregation
converts to the configured business timezone via ``zoneinfo`` (DST-aware), so
day boundaries align to the business day, not UTC midnight.
"""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo


def business_date(ts: float, tz: str) -> str:
    """Return the business-timezone calendar date (ISO) for an epoch timestamp."""
    return datetime.fromtimestamp(ts, tz=ZoneInfo(tz)).date().isoformat()


def today_start_epoch(tz: str) -> float:
    """Return the epoch timestamp of the start of today in ``tz``."""
    now = datetime.now(ZoneInfo(tz))
    start = datetime(now.year, now.month, now.day, tzinfo=now.tzinfo)
    return start.timestamp()


def today_date(tz: str) -> str:
    """Return today's date (ISO) in ``tz``."""
    return datetime.now(ZoneInfo(tz)).date().isoformat()
