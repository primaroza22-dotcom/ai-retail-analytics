"""Time-series-aware evaluation.

Forecasting uses chronological (not random) splits. Metrics: MAE, RMSE, MAPE,
WAPE. MAPE is guarded against near-zero actuals.
"""

from __future__ import annotations

import math

import numpy as np


def chronological_split(values: list[float], test_fraction: float = 0.2, min_test: int = 7) -> int:
    """Return the index at which the test period begins (chronological)."""
    n = len(values)
    test_len = max(min_test, int(n * test_fraction))
    test_len = min(test_len, n - 1)
    return n - test_len


def mae(actual: list[float], predicted: list[float]) -> float:
    return float(np.mean(np.abs(np.array(actual) - np.array(predicted))))


def rmse(actual: list[float], predicted: list[float]) -> float:
    return float(np.sqrt(np.mean((np.array(actual) - np.array(predicted)) ** 2)))


def mape(actual: list[float], predicted: list[float]) -> float | None:
    denom = np.array([abs(a) for a in actual])
    if np.all(denom == 0):
        return None
    mask = denom != 0
    return float(np.mean(np.abs((np.array(actual)[mask] - np.array(predicted)[mask]) / denom[mask])) * 100)


def wape(actual: list[float], predicted: list[float]) -> float | None:
    denom = sum(abs(a) for a in actual)
    if denom == 0:
        return None
    return float(sum(abs(a - p) for a, p in zip(actual, predicted)) / denom * 100)


def forecast_metrics(actual: list[float], predicted: list[float]) -> dict:
    return {
        "mae": mae(actual, predicted),
        "rmse": rmse(actual, predicted),
        "mape": mape(actual, predicted),
        "wape": wape(actual, predicted),
        "n": len(actual),
    }
