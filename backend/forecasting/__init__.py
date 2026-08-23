"""Forecasting + AI analytics foundation (Sprint 13).

Pure, deterministic analytics and forecasting over daily records. No deep
learning; the model is compared honestly against baselines.
"""

from .aggregation import aggregate_daily
from .anomaly import detect_anomalies
from .baselines import moving_average, naive, seasonal_naive
from .correlation import pearson, transaction_rate
from .engine import MODEL_NAMES, evaluate_candidates, forecast_series
from .evaluation import chronological_split, mae, rmse, wape
from .features import build_design_matrix, lag, rolling_mean
from .insights import generate_insights
from .model import LinearRegressionModel
from .records import MIN_HISTORY, TARGETS, DailyRecord, extract_series
from .timezone import business_date, today_date, today_start_epoch

__all__ = [
    "DailyRecord",
    "LinearRegressionModel",
    "MIN_HISTORY",
    "MODEL_NAMES",
    "TARGETS",
    "aggregate_daily",
    "build_design_matrix",
    "business_date",
    "chronological_split",
    "detect_anomalies",
    "evaluate_candidates",
    "extract_series",
    "forecast_series",
    "generate_insights",
    "lag",
    "mae",
    "moving_average",
    "naive",
    "pearson",
    "rmse",
    "rolling_mean",
    "seasonal_naive",
    "today_date",
    "today_start_epoch",
    "transaction_rate",
    "wape",
]
