"""Linear regression forecast model (calendar + trend features).

A deliberately simple, interpretable model. It is compared against baselines;
if it does not beat them, the better baseline is used. Implemented with NumPy
(normal equations + ridge) so no extra ML dependency is required.
"""

from __future__ import annotations

import numpy as np


class LinearRegressionModel:
    """Linear model over ``[day_index, 6 day-of-week dummies]``."""

    name = "linear_regression"
    version = "1"

    def __init__(self, ridge: float = 1e-3) -> None:
        self._ridge = ridge
        self.coef_: np.ndarray | None = None

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        Xb = np.column_stack([np.ones(len(X)), X])
        a = Xb.T @ Xb + self._ridge * np.eye(Xb.shape[1])
        b = Xb.T @ y
        self.coef_ = np.linalg.solve(a, b)

    def predict(self, X: np.ndarray) -> np.ndarray:
        if self.coef_ is None:
            raise RuntimeError("model is not fitted")
        Xb = np.column_stack([np.ones(len(X)), X])
        return Xb @ self.coef_
