from __future__ import annotations

from typing import Any

import numpy as np

from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)


class RegressionMetrics:

    @staticmethod
    def calculate(
        y_true,
        y_pred
    ) -> dict[str, Any]:

        true_values = np.asarray(
            y_true,
            dtype=float
        )

        predicted_values = np.asarray(
            y_pred,
            dtype=float
        )

        if true_values.shape != predicted_values.shape:
            raise ValueError(
                "y_true y y_pred deben tener "
                "la misma dimensión"
            )

        if true_values.size == 0:
            raise ValueError(
                "No existen datos para calcular métricas"
            )

        valid_mask = (
            np.isfinite(true_values)
            &
            np.isfinite(predicted_values)
        )

        true_values = (
            true_values[
                valid_mask
            ]
        )

        predicted_values = (
            predicted_values[
                valid_mask
            ]
        )

        if true_values.size == 0:
            raise ValueError(
                "No existen valores válidos "
                "para calcular métricas"
            )

        mae = mean_absolute_error(
            true_values,
            predicted_values
        )

        mse = mean_squared_error(
            true_values,
            predicted_values
        )

        rmse = float(
            np.sqrt(mse)
        )

        mape = RegressionMetrics._mape(
            true_values,
            predicted_values
        )

        smape = RegressionMetrics._smape(
            true_values,
            predicted_values
        )

        if len(true_values) >= 2:
            r2 = r2_score(
                true_values,
                predicted_values
            )
        else:
            r2 = None

        return {
            "mae": float(mae),
            "mse": float(mse),
            "rmse": float(rmse),
            "mape": (
                float(mape)
                if mape is not None
                else None
            ),
            "smape": float(smape),
            "r2": (
                float(r2)
                if r2 is not None
                else None
            ),
            "samples": int(
                len(true_values)
            )
        }

    @staticmethod
    def _mape(
        y_true: np.ndarray,
        y_pred: np.ndarray
    ) -> float | None:

        non_zero_mask = (
            np.abs(y_true)
            > 1e-12
        )

        if not np.any(
            non_zero_mask
        ):
            return None

        values = (
            np.abs(
                (
                    y_true[
                        non_zero_mask
                    ]
                    -
                    y_pred[
                        non_zero_mask
                    ]
                )
                /
                y_true[
                    non_zero_mask
                ]
            )
            * 100
        )

        return float(
            np.mean(values)
        )

    @staticmethod
    def _smape(
        y_true: np.ndarray,
        y_pred: np.ndarray
    ) -> float:

        denominator = (
            np.abs(y_true)
            +
            np.abs(y_pred)
        )

        valid_mask = (
            denominator
            > 1e-12
        )

        if not np.any(
            valid_mask
        ):
            return 0.0

        values = (
            200
            *
            np.abs(
                y_pred[
                    valid_mask
                ]
                -
                y_true[
                    valid_mask
                ]
            )
            /
            denominator[
                valid_mask
            ]
        )

        return float(
            np.mean(values)
        )