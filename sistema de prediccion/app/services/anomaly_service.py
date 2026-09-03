from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ml.monitoring.anomaly_detector import (
    AnomalyDetector,
)

from app.models.prediction import (
    Prediction,
    PredictionResult,
)

from app.repositories.anomaly_repository import (
    AnomalyRepository,
)

from app.repositories.business_series_repository import (
    BusinessSeriesRepository,
)

from app.repositories.notification_repository import (
    NotificationRepository,
)


class AnomalyService:

    def __init__(self):

        self.detector = (
            AnomalyDetector()
        )

    def scan_prediction_errors(
        self,
        db: Session,
        business_series_id: int | None,
        model_id: int | None,
        limit: int,
        minimum_observations: int,
        z_threshold: float,
        iqr_multiplier: float
    ) -> dict:

        if business_series_id is not None:

            business_series = (
                BusinessSeriesRepository
                .get_by_id(
                    db,
                    business_series_id
                )
            )

            if not business_series:

                raise HTTPException(
                    status_code=404,
                    detail=(
                        "Serie de negocio "
                        "no encontrada"
                    )
                )

        statement = (
            select(
                PredictionResult,
                Prediction
            )
            .join(
                Prediction,
                Prediction.id
                == PredictionResult.prediction_id
            )
            .where(
                PredictionResult.actual_value.is_not(
                    None
                )
            )
            .order_by(
                PredictionResult.prediction_date.desc()
            )
        )

        if business_series_id is not None:

            statement = statement.where(
                Prediction.business_series_id
                == business_series_id
            )

        if model_id is not None:

            statement = statement.where(
                Prediction.model_id
                == model_id
            )

        statement = statement.limit(
            limit
        )

        rows = list(
            db.execute(
                statement
            ).all()
        )

        rows = list(
            reversed(
                rows
            )
        )

        if (
            len(rows)
            < minimum_observations
        ):

            return {
                "business_series_id": (
                    business_series_id
                ),
                "observations_analyzed": (
                    len(
                        rows
                    )
                ),
                "minimum_observations_required": (
                    minimum_observations
                ),
                "anomalies_detected": 0,
                "anomalies_created": 0,
                "anomalies_existing": 0,
                "notifications_created": 0,
                "anomalies": []
            }

        predicted_values = [
            float(
                result.predicted_value
            )
            for result, prediction
            in rows
        ]

        actual_values = [
            float(
                result.actual_value
            )
            for result, prediction
            in rows
        ]

        detections = (
            self.detector
            .detect_prediction_errors(
                predicted_values=(
                    predicted_values
                ),
                actual_values=(
                    actual_values
                ),
                z_threshold=(
                    z_threshold
                ),
                iqr_multiplier=(
                    iqr_multiplier
                ),
                minimum_observations=(
                    minimum_observations
                )
            )
        )

        created_anomalies = []

        existing_count = 0
        notifications_created = 0

        for detection in detections:

            result, prediction = rows[
                detection[
                    "index"
                ]
            ]

            for method in detection[
                "methods"
            ]:

                existing = (
                    AnomalyRepository
                    .get_existing(
                        db=db,
                        prediction_result_id=(
                            result.id
                        ),
                        anomaly_type=(
                            "prediction_error"
                        ),
                        method=method
                    )
                )

                if existing:

                    existing_count += 1

                    continue

                actual_value = float(
                    result.actual_value
                )

                predicted_value = float(
                    result.predicted_value
                )

                deviation = (
                    actual_value
                    -
                    predicted_value
                )

                anomaly = (
                    AnomalyRepository.create(
                        db=db,
                        business_series_id=(
                            prediction
                            .business_series_id
                        ),
                        model_id=(
                            prediction.model_id
                        ),
                        prediction_id=(
                            prediction.id
                        ),
                        prediction_result_id=(
                            result.id
                        ),
                        anomaly_type=(
                            "prediction_error"
                        ),
                        method=method,
                        observed_value=(
                            actual_value
                        ),
                        expected_value=(
                            predicted_value
                        ),
                        deviation=float(
                            deviation
                        ),
                        score=(
                            float(
                                detection[
                                    "z_score"
                                ]
                            )
                            if method
                            == "zscore"
                            else float(
                                detection[
                                    "absolute_error"
                                ]
                            )
                        ),
                        severity=(
                            detection[
                                "severity"
                            ]
                        ),
                        status="open",
                        details={
                            "prediction_date": (
                                result
                                .prediction_date
                                .isoformat()
                            ),
                            "absolute_error": (
                                detection[
                                    "absolute_error"
                                ]
                            ),
                            "z_score": (
                                detection[
                                    "z_score"
                                ]
                            ),
                            "iqr_upper_bound": (
                                detection[
                                    "iqr_upper_bound"
                                ]
                            ),
                            "mean_absolute_error": (
                                detection[
                                    "mean_absolute_error"
                                ]
                            ),
                            "std_absolute_error": (
                                detection[
                                    "std_absolute_error"
                                ]
                            )
                        }
                    )
                )

                created_anomalies.append(
                    anomaly
                )

                self._create_notification(
                    db=db,
                    anomaly=anomaly,
                    prediction=prediction,
                    result=result
                )

                notifications_created += 1

        return {
            "business_series_id": (
                business_series_id
            ),
            "observations_analyzed": (
                len(
                    rows
                )
            ),
            "minimum_observations_required": (
                minimum_observations
            ),
            "anomalies_detected": (
                len(
                    detections
                )
            ),
            "anomalies_created": (
                len(
                    created_anomalies
                )
            ),
            "anomalies_existing": (
                existing_count
            ),
            "notifications_created": (
                notifications_created
            ),
            "anomalies": (
                created_anomalies
            )
        }

    @staticmethod
    def _create_notification(
        db: Session,
        anomaly,
        prediction,
        result
    ) -> None:

        series_name = None

        if (
            prediction.business_series_id
            is not None
        ):

            business_series = (
                BusinessSeriesRepository
                .get_by_id(
                    db,
                    prediction.business_series_id
                )
            )

            if business_series:

                series_name = (
                    business_series.name
                    or business_series
                    .external_entity_id
                )

        target_name = (
            series_name
            or (
                "serie de demanda"
            )
        )

        priority = (
            anomaly.severity
        )

        if priority == "medium":

            priority = "medium"

        elif priority == "high":

            priority = "high"

        elif priority == "critical":

            priority = "critical"

        else:

            priority = "low"

        title = (
            "Anomalía de demanda detectada"
        )

        message = (
            f"Se detectó un comportamiento "
            f"anómalo en {target_name}. "
            f"Valor esperado: "
            f"{float(result.predicted_value):.2f}. "
            f"Valor real: "
            f"{float(result.actual_value):.2f}."
        )

        suggested_action = (
            "Revisar el comportamiento de la "
            "demanda y verificar si existen "
            "promociones, feriados, eventos, "
            "errores de registro o cambios "
            "operativos. Evaluar también el "
            "desempeño del modelo."
        )

        NotificationRepository.create(
            db=db,
            user_id=(
                prediction.user_id
            ),
            recipient_role=None,
            category="demand",
            notification_type=(
                "demand_anomaly"
            ),
            title=title,
            message=message,
            priority=priority,
            requires_action=True,
            suggested_action=(
                suggested_action
            ),
            entity_type="anomaly",
            entity_id=str(
                anomaly.id
            ),
            payload={
                "anomaly_id": anomaly.id,
                "prediction_id": (
                    prediction.id
                ),
                "prediction_result_id": (
                    result.id
                ),
                "business_series_id": (
                    prediction
                    .business_series_id
                ),
                "model_id": (
                    prediction.model_id
                ),
                "prediction_date": (
                    result
                    .prediction_date
                    .isoformat()
                ),
                "predicted_value": float(
                    result.predicted_value
                ),
                "actual_value": float(
                    result.actual_value
                ),
                "deviation": (
                    anomaly.deviation
                ),
                "severity": (
                    anomaly.severity
                ),
                "method": (
                    anomaly.method
                )
            }
        )