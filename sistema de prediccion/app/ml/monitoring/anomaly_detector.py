from __future__ import annotations

from typing import Any

import numpy as np


class AnomalyDetector:

    @staticmethod
    def detect_prediction_errors(
        predicted_values,
        actual_values,
        z_threshold: float = 3.0,
        iqr_multiplier: float = 1.5,
        minimum_observations: int = 10
    ) -> list[dict[str, Any]]:

        predicted = np.asarray(
            predicted_values,
            dtype=float
        )

        actual = np.asarray(
            actual_values,
            dtype=float
        )

        if predicted.shape != actual.shape:

            raise ValueError(
                "predicted_values y actual_values "
                "deben tener la misma dimensión"
            )

        valid_mask = (
            np.isfinite(predicted)
            &
            np.isfinite(actual)
        )

        predicted = predicted[
            valid_mask
        ]

        actual = actual[
            valid_mask
        ]

        if (
            len(predicted)
            < minimum_observations
        ):

            return []

        errors = (
            actual
            -
            predicted
        )

        absolute_errors = np.abs(
            errors
        )

        mean_error = float(
            np.mean(
                absolute_errors
            )
        )

        std_error = float(
            np.std(
                absolute_errors,
                ddof=0
            )
        )

        q1 = float(
            np.percentile(
                absolute_errors,
                25
            )
        )

        q3 = float(
            np.percentile(
                absolute_errors,
                75
            )
        )

        iqr = (
            q3
            -
            q1
        )

        upper_iqr = (
            q3
            +
            (
                iqr_multiplier
                *
                iqr
            )
        )

        anomalies = []

        for index in range(
            len(
                absolute_errors
            )
        ):

            absolute_error = float(
                absolute_errors[
                    index
                ]
            )

            error = float(
                errors[
                    index
                ]
            )

            if std_error > 0:

                z_score = (
                    (
                        absolute_error
                        -
                        mean_error
                    )
                    /
                    std_error
                )

            else:

                z_score = 0.0

            z_anomaly = (
                z_score
                >= z_threshold
            )

            iqr_anomaly = (
                absolute_error
                > upper_iqr
                if iqr > 0
                else False
            )

            if not (
                z_anomaly
                or iqr_anomaly
            ):

                continue

            methods = []

            if z_anomaly:
                methods.append(
                    "zscore"
                )

            if iqr_anomaly:
                methods.append(
                    "iqr"
                )

            severity = (
                AnomalyDetector
                .calculate_severity(
                    absolute_error=(
                        absolute_error
                    ),
                    mean_error=(
                        mean_error
                    ),
                    std_error=(
                        std_error
                    ),
                    z_score=(
                        z_score
                    )
                )
            )

            anomalies.append(
                {
                    "index": index,
                    "error": error,
                    "absolute_error": (
                        absolute_error
                    ),
                    "z_score": float(
                        z_score
                    ),
                    "iqr_upper_bound": (
                        float(
                            upper_iqr
                        )
                    ),
                    "methods": methods,
                    "severity": severity,
                    "mean_absolute_error": (
                        mean_error
                    ),
                    "std_absolute_error": (
                        std_error
                    )
                }
            )

        return anomalies

    @staticmethod
    def calculate_severity(
        absolute_error: float,
        mean_error: float,
        std_error: float,
        z_score: float
    ) -> str:

        if z_score >= 5:

            return "critical"

        if z_score >= 4:

            return "high"

        if z_score >= 3:

            return "medium"

        if (
            std_error > 0
            and absolute_error
            >
            (
                mean_error
                +
                2 * std_error
            )
        ):

            return "medium"

        return "low"