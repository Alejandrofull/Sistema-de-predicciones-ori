from __future__ import annotations

from typing import Any

import numpy as np

from app.ml.core.metrics import (
    RegressionMetrics,
)


class PerformanceMonitor:

    @staticmethod
    def calculate(
        actual_values,
        predicted_values
    ) -> dict[str, Any]:

        actual = np.asarray(
            actual_values,
            dtype=float
        )

        predicted = np.asarray(
            predicted_values,
            dtype=float
        )

        if actual.shape != predicted.shape:
            raise ValueError(
                "actual_values y predicted_values "
                "deben tener la misma dimensión"
            )

        if actual.size == 0:
            raise ValueError(
                "No existen observaciones "
                "para evaluar"
            )

        valid_mask = (
            np.isfinite(actual)
            &
            np.isfinite(predicted)
        )

        actual = actual[
            valid_mask
        ]

        predicted = predicted[
            valid_mask
        ]

        if actual.size == 0:
            raise ValueError(
                "No existen observaciones "
                "válidas para evaluar"
            )

        metrics = (
            RegressionMetrics.calculate(
                y_true=actual,
                y_pred=predicted
            )
        )

        errors = (
            predicted
            -
            actual
        )

        absolute_errors = np.abs(
            errors
        )

        bias = float(
            np.mean(
                errors
            )
        )

        mean_absolute_error = float(
            np.mean(
                absolute_errors
            )
        )

        max_absolute_error = float(
            np.max(
                absolute_errors
            )
        )

        median_absolute_error = float(
            np.median(
                absolute_errors
            )
        )

        under_predictions = int(
            np.sum(
                predicted < actual
            )
        )

        over_predictions = int(
            np.sum(
                predicted > actual
            )
        )

        exact_predictions = int(
            np.sum(
                np.isclose(
                    predicted,
                    actual
                )
            )
        )

        total = int(
            len(
                actual
            )
        )

        return {
            **metrics,
            "bias": bias,
            "mean_absolute_error": (
                mean_absolute_error
            ),
            "median_absolute_error": (
                median_absolute_error
            ),
            "max_absolute_error": (
                max_absolute_error
            ),
            "under_predictions": (
                under_predictions
            ),
            "over_predictions": (
                over_predictions
            ),
            "exact_predictions": (
                exact_predictions
            ),
            "under_prediction_percentage": (
                round(
                    (
                        under_predictions
                        / total
                        * 100
                    ),
                    4
                )
            ),
            "over_prediction_percentage": (
                round(
                    (
                        over_predictions
                        / total
                        * 100
                    ),
                    4
                )
            )
        }

    @staticmethod
    def evaluate_health(
        current_metrics: dict[str, Any],
        baseline_metrics: dict[str, Any] | None = None,
        rmse_degradation_threshold: float = 0.20,
        mape_threshold: float = 20.0
    ) -> dict[str, Any]:

        warnings = []

        current_rmse = (
            current_metrics.get(
                "rmse"
            )
        )

        current_mape = (
            current_metrics.get(
                "mape"
            )
        )

        rmse_degradation = None

        if baseline_metrics:

            baseline_rmse = (
                baseline_metrics.get(
                    "rmse"
                )
            )

            if (
                baseline_rmse is not None
                and current_rmse is not None
                and float(
                    baseline_rmse
                ) > 0
            ):

                rmse_degradation = (
                    (
                        float(
                            current_rmse
                        )
                        -
                        float(
                            baseline_rmse
                        )
                    )
                    /
                    float(
                        baseline_rmse
                    )
                )

                if (
                    rmse_degradation
                    >
                    rmse_degradation_threshold
                ):

                    warnings.append(
                        {
                            "code": (
                                "rmse_degradation"
                            ),
                            "message": (
                                "El RMSE en producción "
                                "supera significativamente "
                                "el RMSE de evaluación."
                            ),
                            "degradation_percentage": (
                                round(
                                    rmse_degradation
                                    * 100,
                                    4
                                )
                            )
                        }
                    )

        if (
            current_mape is not None
            and float(
                current_mape
            ) > mape_threshold
        ):

            warnings.append(
                {
                    "code": (
                        "high_mape"
                    ),
                    "message": (
                        "El MAPE actual supera "
                        "el umbral configurado."
                    ),
                    "current_mape": (
                        float(
                            current_mape
                        )
                    ),
                    "threshold": (
                        mape_threshold
                    )
                }
            )

        bias = (
            current_metrics.get(
                "bias"
            )
        )

        if bias is not None:

            if bias < 0:

                bias_direction = (
                    "underprediction"
                )

            elif bias > 0:

                bias_direction = (
                    "overprediction"
                )

            else:

                bias_direction = (
                    "neutral"
                )

        else:

            bias_direction = None

        if warnings:

            health_status = (
                "degraded"
            )

            retraining_recommended = (
                True
            )

        else:

            health_status = (
                "healthy"
            )

            retraining_recommended = (
                False
            )

        return {
            "status": (
                health_status
            ),
            "retraining_recommended": (
                retraining_recommended
            ),
            "rmse_degradation": (
                rmse_degradation
            ),
            "bias_direction": (
                bias_direction
            ),
            "warnings": (
                warnings
            )
        }