"""Baseline forecasting models.

Simple, deterministic baselines that any more advanced model must beat.
"""

from __future__ import annotations

import numpy as np

DEFAULT_SEASON = 7


def naive(values: list[float]) -> float:
    """Tomorrow equals today (last observed value)."""
    return float(values[-1])


def seasonal_naive(values: list[float], season: int = DEFAULT_SEASON) -> float:
    """Tomorrow equals the same weekday from the previous week."""
    if len(values) < season:
        return naive(values)
    return float(values[-season])


def moving_average(values: list[float], window: int = DEFAULT_SEASON) -> float:
    """Tomorrow equals the mean of the last ``window`` observed values."""
    window = min(window, len(values))
    recent = values[-window:]
    return float(np.mean(recent))


def backtest_naive(values: list[float], split: int) -> list[float]:
    return [values[split + i - 1] for i in range(0, len(values) - split)]


def backtest_seasonal_naive(values: list[float], split: int, season: int = DEFAULT_SEASON) -> list[float]:
    result: list[float] = []
    for i in range(split, len(values)):
        if i - season >= 0:
            result.append(values[i - season])
        else:
            result.append(values[i - 1])
    return result


def backtest_moving_average(values: list[float], split: int, window: int = DEFAULT_SEASON) -> list[float]:
    result: list[float] = []
    for i in range(split, len(values)):
        window_i = min(window, i)
        result.append(float(np.mean(values[i - window_i : i])))
    return result
