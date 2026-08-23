"""Simple anomaly detection using a rolling mean / standard-deviation window."""

from __future__ import annotations

import numpy as np


def detect_anomalies(
    dates: list[str],
    values: list[float],
    *,
    window: int = 7,
    threshold: float = 2.5,
) -> list[dict]:
    """Return anomalies where the value deviates from its rolling window by
    more than ``threshold`` standard deviations.

    A flat (zero-variance) window that is followed by a different value is also
    treated as an anomaly (deviation from a constant baseline).
    """
    anomalies: list[dict] = []
    for i in range(window, len(values)):
        recent = values[i - window : i]
        mean = float(np.mean(recent))
        std = float(np.std(recent))
        if std == 0:
            if values[i] == mean:
                continue
            z = 3.0 if values[i] > mean else -3.0
            direction = "high" if values[i] > mean else "low"
            severity = "high"
        else:
            z = (values[i] - mean) / std
            if abs(z) < threshold:
                continue
            direction = "high" if z > 0 else "low"
            severity = "high" if abs(z) >= threshold * 1.5 else "medium"
        anomalies.append(
            {
                "date": dates[i],
                "actual": values[i],
                "expected": mean,
                "deviation": values[i] - mean,
                "z_score": z,
                "direction": direction,
                "severity": severity,
            }
        )
    return anomalies
