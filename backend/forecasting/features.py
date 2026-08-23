"""Feature engineering for daily time series.

Features are calendar- and lag/rolling-based. All lag/rolling features use only
past values (never the current or future value), so no target leakage occurs.
"""

from __future__ import annotations

import datetime as _dt

import numpy as np


def parse_date(date: str) -> _dt.date:
    return _dt.date.fromisoformat(date)


def day_of_week(date: str) -> int:
    # Monday = 0 .. Sunday = 6
    return parse_date(date).weekday()


def is_weekend(date: str) -> bool:
    return parse_date(date).weekday() >= 5


def lag(values: list[float], n: int) -> list[float | None]:
    """Return the series shifted by ``n`` (None for the first ``n`` entries)."""
    result: list[float | None] = [None] * len(values)
    for i in range(n, len(values)):
        result[i] = values[i - n]
    return result


def rolling_mean(values: list[float], window: int) -> list[float | None]:
    """Rolling mean of the ``window`` values strictly before the current index."""
    result: list[float | None] = [None] * len(values)
    for i in range(len(values)):
        if i >= window:
            result[i] = float(np.mean(values[i - window : i]))
    return result


def build_design_matrix(dates: list[str], base_date: str) -> np.ndarray:
    """Design matrix (without bias) for the linear forecast model.

    Columns: ``day_index`` (days since base date) and 6 day-of-week dummies
    (Monday..Saturday; Sunday is the reference category).
    """
    base = parse_date(base_date)
    rows = []
    for date in dates:
        d = parse_date(date)
        day_index = (d - base).days
        dow = d.weekday()
        dummies = [1.0 if dow == i else 0.0 for i in range(6)]
        rows.append([float(day_index), *dummies])
    return np.array(rows, dtype=float)
