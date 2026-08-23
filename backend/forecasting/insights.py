"""Deterministic AI insights derived from actual metrics (no fabricated claims)."""

from __future__ import annotations

import numpy as np

from .records import DailyRecord

_METRIC_LABELS = {
    "traffic": "Traffic",
    "transactions": "Transactions",
    "net_sales": "Sales",
    "items_sold": "Items sold",
    "avg_transaction_value": "Average transaction value",
    "avg_dwell": "Average dwell time",
}


def generate_insights(records: list[DailyRecord]) -> list[dict]:
    """Compare the last 7 days against the previous 7 days and surface trends."""
    ordered = sorted(records, key=lambda r: r.date)
    if len(ordered) < 14:
        return []

    insights: list[dict] = []
    for metric in ("traffic", "transactions", "net_sales", "items_sold", "avg_transaction_value", "avg_dwell"):
        values = []
        for record in ordered:
            if metric == "avg_dwell":
                values.append(record.avg_dwell if record.avg_dwell is not None else 0.0)
            else:
                values.append(record.value(metric))
        recent = values[-7:]
        previous = values[-14:-7]
        recent_mean = float(np.mean(recent))
        previous_mean = float(np.mean(previous))
        if previous_mean == 0:
            continue
        change = (recent_mean - previous_mean) / abs(previous_mean)
        if change > 0.1:
            direction = "up"
        elif change < -0.1:
            direction = "down"
        else:
            continue
        insights.append(
            {
                "type": "trend",
                "metric": metric,
                "direction": direction,
                "message": f"{_METRIC_LABELS[metric]} is trending {direction} "
                f"({recent_mean:,.2f} vs {previous_mean:,.2f} previous 7-day average).",
            }
        )
    return insights
