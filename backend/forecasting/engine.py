"""Forecast engine: baseline comparison, model selection, and forecasting.

The engine evaluates the naive, seasonal naive, moving average, and linear
regression models chronologically, honestly selects the best by MAE, and
generates a forecast with that model.
"""

from __future__ import annotations

import datetime as _dt

from .baselines import (
    backtest_moving_average,
    backtest_naive,
    backtest_seasonal_naive,
    moving_average,
    naive,
    seasonal_naive,
)
from .evaluation import chronological_split, forecast_metrics
from .features import build_design_matrix
from .model import LinearRegressionModel

MODEL_NAMES = ("naive", "seasonal_naive", "moving_average", "linear_regression")


def _future_dates(last_date: str, horizon: int) -> list[str]:
    base = _dt.date.fromisoformat(last_date)
    return [(base + _dt.timedelta(days=i + 1)).isoformat() for i in range(horizon)]


def evaluate_candidates(dates: list[str], values: list[float]) -> list[dict]:
    """Evaluate all candidate models on the chronological test period."""
    split = chronological_split(values)
    test_actual = values[split:]
    test_dates = dates[split:]
    base_date = dates[0]

    candidates = {
        "naive": backtest_naive(values, split),
        "seasonal_naive": backtest_seasonal_naive(values, split),
        "moving_average": backtest_moving_average(values, split),
    }

    linear = LinearRegressionModel()
    linear.fit(build_design_matrix(dates[:split], base_date), values[:split])
    candidates["linear_regression"] = list(linear.predict(build_design_matrix(test_dates, base_date)))

    results = []
    for name in MODEL_NAMES:
        metrics = forecast_metrics(test_actual, candidates[name])
        results.append(
            {
                "model": name,
                "mae": metrics["mae"],
                "rmse": metrics["rmse"],
                "mape": metrics["mape"],
                "wape": metrics["wape"],
                "n_test": metrics["n"],
            }
        )
    results.sort(key=lambda r: r["mae"])
    return results


def forecast_series(dates: list[str], values: list[float], horizon: int) -> dict:
    """Generate a forecast using the best (lowest-MAE) candidate."""
    evaluation = evaluate_candidates(dates, values)
    best = evaluation[0]["model"]
    future_dates = _future_dates(dates[-1], horizon)

    if best == "naive":
        predicted = [naive(values)] * horizon
    elif best == "seasonal_naive":
        predicted = [seasonal_naive(values)] * horizon
    elif best == "moving_average":
        predicted = [moving_average(values)] * horizon
    else:
        base_date = dates[0]
        linear = LinearRegressionModel()
        linear.fit(build_design_matrix(dates, base_date), values)
        predicted = [float(x) for x in linear.predict(build_design_matrix(future_dates, base_date))]

    points = [
        {"date": future_dates[i], "predicted_value": max(0.0, predicted[i])}
        for i in range(horizon)
    ]
    return {"model": best, "evaluation": evaluation, "points": points}
