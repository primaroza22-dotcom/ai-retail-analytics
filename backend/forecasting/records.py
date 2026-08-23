"""Daily analytics records and forecasting targets.

A ``DailyRecord`` is the standardized daily grain that forecasting and
analytics consume. It is produced either from the database (aggregation) or
from deterministic synthetic data in tests.
"""

from __future__ import annotations

from dataclasses import dataclass

# Forecast targets (commercially meaningful, deterministic to aggregate).
TARGETS = ("traffic", "transactions", "net_sales", "items_sold", "avg_transaction_value")

# Minimum daily observations (calendar weeks) required before forecasting.
MIN_HISTORY = 21


@dataclass(frozen=True)
class DailyRecord:
    """One day of normalized metrics.

    ``traffic`` is defined as the number of zone-entry events for the day (a
    camera-scopable visit count), NOT an identified-person count.
    """

    date: str  # ISO date "YYYY-MM-DD" in the configured business timezone
    traffic: float = 0.0
    transactions: float = 0.0
    net_sales: float = 0.0
    items_sold: float = 0.0
    avg_transaction_value: float | None = None
    avg_dwell: float | None = None

    def value(self, target: str) -> float:
        if target == "avg_transaction_value":
            return self.avg_transaction_value if self.avg_transaction_value is not None else 0.0
        return float(getattr(self, target, 0.0))


def extract_series(records: list[DailyRecord], target: str) -> list[tuple[str, float]]:
    """Return chronological ``(date, value)`` pairs for a target."""
    ordered = sorted(records, key=lambda r: r.date)
    return [(record.date, record.value(target)) for record in ordered]
