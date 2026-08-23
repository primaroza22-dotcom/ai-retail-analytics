"""Correlation and ratio analytics.

Correlation is NOT causation; these are diagnostic indicators only.
"""

from __future__ import annotations

import numpy as np


def pearson(x: list[float], y: list[float]) -> float | None:
    if len(x) < 2 or len(x) != len(y):
        return None
    xs = np.array(x, dtype=float)
    ys = np.array(y, dtype=float)
    if np.std(xs) == 0 or np.std(ys) == 0:
        return None
    return float(np.corrcoef(xs, ys)[0, 1])


def transaction_rate(traffic: float, transactions: float) -> float | None:
    """Operational ratio: transactions / traffic (NOT person-level conversion)."""
    if traffic == 0:
        return None
    return transactions / traffic
