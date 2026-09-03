from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from statsmodels.tsa.arima.model import (
    ARIMA
)

from app.ml.core.metrics import (
    RegressionMetrics
)


class ArimaDemandModel:

    model_name = "arima"

    def __init__(
        self,
        order: tuple[int, int, int] = (
            5,
            1,
            1
        )
    ):
        self.order = order

        self.model = None
        self.fitted_model = None

    def fit(
        self,
        y
    ) -> "ArimaDemandModel":

        series = self._prepare_series(
            y
        )

        if len(series) < 10:
            raise ValueError(
                "ARIMA necesita al menos "
                "10 observaciones"
            )

        self.model = ARIMA(
            series,
            order=self.order
        )

        self.fitted_model = (
            self.model.fit()
        )

        return self

    def predict(
        self,
        steps: int
    ) -> np.ndarray:

        if self.fitted_model is None:
            raise RuntimeError(
                "El modelo ARIMA no ha sido entrenado"
            )

        if steps <= 0:
            raise ValueError(
                "steps debe ser mayor que 0"
            )

        forecast = (
            self.fitted_model
            .forecast(
                steps=steps
            )
        )

        return np.asarray(
            forecast,
            dtype=float
        )

    def evaluate(
        self,
        train_y,
        test_y
    ) -> dict[str, Any]:

        self.fit(
            train_y
        )

        predictions = self.predict(
            len(test_y)
        )

        metrics = (
            RegressionMetrics
            .calculate(
                test_y,
                predictions
            )
        )

        return {
            "model": self.model_name,
            "parameters": {
                "order": list(
                    self.order
                )
            },
            "metrics": metrics,
            "predictions": (
                predictions.tolist()
            )
        }

    @staticmethod
    def _prepare_series(
        y
    ) -> pd.Series:

        series = pd.Series(
            y
        )

        series = pd.to_numeric(
            series,
            errors="coerce"
        )

        series = (
            series
            .replace(
                [
                    np.inf,
                    -np.inf
                ],
                np.nan
            )
            .dropna()
            .reset_index(
                drop=True
            )
        )

        if series.empty:
            raise ValueError(
                "La serie objetivo no contiene "
                "valores numéricos válidos"
            )

        return series.astype(
            float
        )