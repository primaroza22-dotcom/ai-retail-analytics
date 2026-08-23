"""Timezone boundary tests (Sprint 14).

Verifies that daily aggregation day boundaries align to the business timezone,
not UTC midnight, including DST-aware timezones.
"""

from __future__ import annotations

import datetime as dt

from backend.forecasting import business_date, today_date, today_start_epoch


def _utc(y: int, m: int, d: int, hh: int, mm: int, ss: int) -> float:
    return dt.datetime(y, m, d, hh, mm, ss, tzinfo=dt.timezone.utc).timestamp()


def test_business_date_jakarta_midnight_boundary() -> None:
    tz = "Asia/Jakarta"  # UTC+7, no DST
    # 16:59:59 UTC -> 23:59:59 Jakarta -> same day
    assert business_date(_utc(2026, 1, 1, 16, 59, 59), tz) == "2026-01-01"
    # 17:00:00 UTC -> 00:00:00 Jakarta next day -> boundary crossed
    assert business_date(_utc(2026, 1, 1, 17, 0, 0), tz) == "2026-01-02"


def test_business_date_dst_aware_timezone() -> None:
    tz = "America/New_York"  # EDT = UTC-4 in July
    assert business_date(_utc(2026, 7, 1, 3, 59, 59), tz) == "2026-06-30"
    assert business_date(_utc(2026, 7, 1, 4, 0, 0), tz) == "2026-07-01"


def test_today_helpers_consistent() -> None:
    tz = "UTC"
    assert today_date(tz) == today_date(tz)
    start = today_start_epoch(tz)
    assert business_date(start, tz) == today_date(tz)
