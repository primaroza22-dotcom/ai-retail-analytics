"""Forecasting + AI analytics pure-function tests (Sprint 13).

All tests use deterministic synthetic daily data (test-only, clearly not real).
"""

from __future__ import annotations

import datetime as dt

import pytest

from backend.forecasting import (
    MIN_HISTORY,
    MODEL_NAMES,
    DailyRecord,
    build_design_matrix,
    chronological_split,
    detect_anomalies,
    evaluate_candidates,
    forecast_series,
    generate_insights,
    lag,
    mae,
    moving_average,
    naive,
    pearson,
    rmse,
    rolling_mean,
    seasonal_naive,
    transaction_rate,
)


def _dates(n: int) -> list[str]:
    base = dt.date(2026, 1, 1)
    return [(base + dt.timedelta(days=i)).isoformat() for i in range(n)]


def _weekly_trend(n: int = 28) -> list[float]:
    return [100.0 + 2.0 * i + (20.0 if i % 7 >= 5 else 0.0) for i in range(n)]


def _records(dates: list[str], net_sales=None) -> list[DailyRecord]:
    return [
        DailyRecord(
            date=d,
            traffic=100 + i,
            transactions=10 + i,
            net_sales=(net_sales[i] if net_sales else 1000 + 10 * i),
        )
        for i, d in enumerate(dates)
    ]


# --- Features ---


def test_lag_feature() -> None:
    values = [1.0, 2.0, 3.0, 4.0]
    assert lag(values, 1) == [None, 1.0, 2.0, 3.0]
    assert lag(values, 2) == [None, None, 1.0, 2.0]


def test_rolling_mean_uses_only_past() -> None:
    values = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]
    result = rolling_mean(values, 3)
    assert result[0:3] == [None, None, None]
    assert result[3] == 2.0  # mean(1,2,3)
    assert result[7] == 6.0  # mean(5,6,7) — excludes current (8.0)


def test_design_matrix_shape() -> None:
    dates = _dates(7)
    X = build_design_matrix(dates, dates[0])
    assert X.shape == (7, 7)  # day_index + 6 weekday dummies


# --- Baselines ---


def test_naive() -> None:
    assert naive([1.0, 2.0, 3.0]) == 3.0


def test_seasonal_naive() -> None:
    values = [float(i) for i in range(1, 11)]  # 1..10
    assert seasonal_naive(values, season=7) == 4.0  # values[-7] = values[3] = 4


def test_moving_average() -> None:
    assert moving_average([1.0, 2.0, 3.0], window=3) == 2.0


# --- Evaluation ---


def test_chronological_split_is_temporal() -> None:
    values = list(range(30))
    split = chronological_split(values)
    assert 0 < split < 30
    assert split >= 30 - 7


def test_mae_rmse() -> None:
    assert mae([1.0, 2.0], [1.0, 2.0]) == 0.0
    assert mae([1.0, 3.0], [1.0, 1.0]) == 1.0
    assert rmse([0.0, 0.0], [3.0, 4.0]) == pytest.approx(3.5355339)


# --- Forecast engine ---


def test_evaluate_candidates_returns_all_models() -> None:
    dates = _dates(28)
    values = _weekly_trend(28)
    results = evaluate_candidates(dates, values)
    assert {r["model"] for r in results} == set(MODEL_NAMES)
    assert all(r["mae"] >= 0 for r in results)


def test_forecast_series_returns_horizon_points() -> None:
    dates = _dates(28)
    values = _weekly_trend(28)
    result = forecast_series(dates, values, horizon=7)
    assert len(result["points"]) == 7
    assert result["model"] in MODEL_NAMES
    assert all(p["predicted_value"] >= 0 for p in result["points"])


def test_forecast_insufficient_history_guard() -> None:
    assert MIN_HISTORY == 21


# --- Anomaly detection ---


def test_anomaly_detects_spike() -> None:
    dates = _dates(15)
    values = [10.0] * 14 + [100.0]
    anomalies = detect_anomalies(dates, values, window=7)
    assert len(anomalies) >= 1
    assert anomalies[-1]["direction"] == "high"
    assert anomalies[-1]["actual"] == 100.0


def test_anomaly_no_false_positive_on_flat() -> None:
    dates = _dates(15)
    anomalies = detect_anomalies(dates, [10.0] * 15, window=7)
    assert anomalies == []


# --- Correlation / ratio ---


def test_pearson_correlation() -> None:
    xs = [float(i) for i in range(10)]
    ys = [2 * x for x in xs]
    assert pearson(xs, ys) == pytest.approx(1.0)
    zs = [-x for x in xs]
    assert pearson(xs, zs) == pytest.approx(-1.0)


def test_pearson_constant_returns_none() -> None:
    assert pearson([1.0, 1.0, 1.0], [1.0, 2.0, 3.0]) is None


def test_transaction_rate_zero_traffic() -> None:
    assert transaction_rate(0, 5) is None
    assert transaction_rate(10, 5) == 0.5


# --- Insights ---


def test_insights_detect_upward_trend() -> None:
    dates = _dates(28)
    net_sales = [1000.0 + 50.0 * i for i in range(28)]
    records = _records(dates, net_sales=net_sales)
    insights = generate_insights(records)
    sales = [i for i in insights if i["metric"] == "net_sales"]
    assert any(i["direction"] == "up" for i in sales)


def test_insights_empty_for_short_history() -> None:
    assert generate_insights(_records(_dates(10))) == []
