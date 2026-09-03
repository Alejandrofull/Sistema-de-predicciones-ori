from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.ml.monitoring.performance_monitor import (
    PerformanceMonitor,
)

from app.repositories.business_series_repository import (
    BusinessSeriesRepository,
)

from app.repositories.model_evaluation_repository import (
    ModelEvaluationRepository,
)

from app.repositories.model_repository import (
    ModelRepository,
)

from app.repositories.model_version_repository import (
    ModelVersionRepository,
)

from app.repositories.prediction_result_repository import (
    PredictionResultRepository,
)


class PerformanceMonitoringService:

    def __init__(self):

        self.monitor = (
            PerformanceMonitor()
        )

    def get_model_performance(
        self,
        db: Session,
        model_id: int,
        limit: int,
        minimum_observations: int,
        rmse_degradation_threshold: float,
        mape_threshold: float
    ) -> dict:

        model = (
            ModelRepository.get_by_id(
                db,
                model_id
            )
        )

        if not model:

            raise HTTPException(
                status_code=404,
                detail="Modelo no encontrado"
            )

        results = (
            PredictionResultRepository
            .get_with_actual_by_model(
                db=db,
                model_id=(
                    model.id
                ),
                limit=(
                    limit
                )
            )
        )

        baseline_evaluation = (
            ModelEvaluationRepository
            .get_latest_by_model(
                db=db,
                model_id=(
                    model.id
                )
            )
        )

        return (
            self._build_response(
                model_id=(
                    model.id
                ),
                business_series_id=(
                    model.business_series_id
                ),
                model_type=(
                    model.model_type
                ),
                results=(
                    results
                ),
                baseline_evaluation=(
                    baseline_evaluation
                ),
                minimum_observations=(
                    minimum_observations
                ),
                rmse_degradation_threshold=(
                    rmse_degradation_threshold
                ),
                mape_threshold=(
                    mape_threshold
                )
            )
        )

    def get_business_series_performance(
        self,
        db: Session,
        business_series_id: int,
        limit: int,
        minimum_observations: int,
        rmse_degradation_threshold: float,
        mape_threshold: float
    ) -> dict:

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

        active_model = (
            ModelRepository
            .get_active_by_business_series(
                db=db,
                business_series_id=(
                    business_series_id
                )
            )
        )

        if not active_model:

            raise HTTPException(
                status_code=400,
                detail=(
                    "La serie de negocio "
                    "no tiene modelo activo"
                )
            )

        results = (
            PredictionResultRepository
            .get_with_actual_by_business_series(
                db=db,
                business_series_id=(
                    business_series_id
                ),
                limit=(
                    limit
                )
            )
        )

        active_version = (
            ModelVersionRepository
            .get_active_by_model(
                db=db,
                model_id=(
                    active_model.id
                )
            )
        )

        baseline_evaluation = None

        if active_version:

            baseline_evaluation = (
                ModelEvaluationRepository
                .get_latest_by_model_version(
                    db=db,
                    model_version_id=(
                        active_version.id
                    )
                )
            )

        if not baseline_evaluation:

            baseline_evaluation = (
                ModelEvaluationRepository
                .get_latest_by_model(
                    db=db,
                    model_id=(
                        active_model.id
                    )
                )
            )

        return (
            self._build_response(
                model_id=(
                    active_model.id
                ),
                business_series_id=(
                    business_series_id
                ),
                model_type=(
                    active_model.model_type
                ),
                results=(
                    results
                ),
                baseline_evaluation=(
                    baseline_evaluation
                ),
                minimum_observations=(
                    minimum_observations
                ),
                rmse_degradation_threshold=(
                    rmse_degradation_threshold
                ),
                mape_threshold=(
                    mape_threshold
                )
            )
        )

    def get_prediction_performance(
        self,
        db: Session,
        prediction_id: int,
        minimum_observations: int,
        rmse_degradation_threshold: float,
        mape_threshold: float
    ) -> dict:

        from app.repositories.prediction_repository import (
            PredictionRepository,
        )

        prediction = (
            PredictionRepository.get_by_id(
                db,
                prediction_id
            )
        )

        if not prediction:

            raise HTTPException(
                status_code=404,
                detail=(
                    "Predicción no encontrada"
                )
            )

        model = (
            ModelRepository.get_by_id(
                db,
                prediction.model_id
            )
        )

        results = (
            PredictionResultRepository
            .get_with_actual_by_prediction(
                db=db,
                prediction_id=(
                    prediction.id
                )
            )
        )

        baseline_evaluation = None

        if prediction.model_version_id:

            baseline_evaluation = (
                ModelEvaluationRepository
                .get_latest_by_model_version(
                    db=db,
                    model_version_id=(
                        prediction.model_version_id
                    )
                )
            )

        if (
            not baseline_evaluation
            and model
        ):

            baseline_evaluation = (
                ModelEvaluationRepository
                .get_latest_by_model(
                    db=db,
                    model_id=(
                        model.id
                    )
                )
            )

        return (
            self._build_response(
                model_id=(
                    prediction.model_id
                ),
                business_series_id=(
                    prediction.business_series_id
                ),
                model_type=(
                    model.model_type
                    if model
                    else None
                ),
                results=(
                    results
                ),
                baseline_evaluation=(
                    baseline_evaluation
                ),
                minimum_observations=(
                    minimum_observations
                ),
                rmse_degradation_threshold=(
                    rmse_degradation_threshold
                ),
                mape_threshold=(
                    mape_threshold
                )
            )
        )

    def _build_response(
        self,
        model_id: int | None,
        business_series_id: int | None,
        model_type: str | None,
        results: list,
        baseline_evaluation,
        minimum_observations: int,
        rmse_degradation_threshold: float,
        mape_threshold: float
    ) -> dict:

        observations = []

        for result in results:

            if result.actual_value is None:
                continue

            predicted_value = float(
                result.predicted_value
            )

            actual_value = float(
                result.actual_value
            )

            error = (
                predicted_value
                -
                actual_value
            )

            observations.append(
                {
                    "prediction_result_id": (
                        result.id
                    ),
                    "prediction_date": (
                        result.prediction_date
                    ),
                    "predicted_value": (
                        predicted_value
                    ),
                    "actual_value": (
                        actual_value
                    ),
                    "error": (
                        float(
                            error
                        )
                    ),
                    "absolute_error": (
                        float(
                            abs(
                                error
                            )
                        )
                    )
                }
            )

        total = len(
            observations
        )

        sufficient_data = (
            total
            >= minimum_observations
        )

        baseline_metrics = (
            self._serialize_baseline(
                baseline_evaluation
            )
        )

        if not sufficient_data:

            return {
                "model_id": (
                    model_id
                ),
                "business_series_id": (
                    business_series_id
                ),
                "model_type": (
                    model_type
                ),
                "observations_available": (
                    total
                ),
                "minimum_observations_required": (
                    minimum_observations
                ),
                "sufficient_data": (
                    False
                ),
                "metrics": None,
                "baseline_metrics": (
                    baseline_metrics
                ),
                "health": None,
                "observations": (
                    observations
                )
            }

        actual_values = [
            item[
                "actual_value"
            ]
            for item
            in observations
        ]

        predicted_values = [
            item[
                "predicted_value"
            ]
            for item
            in observations
        ]

        metrics = (
            self.monitor.calculate(
                actual_values=(
                    actual_values
                ),
                predicted_values=(
                    predicted_values
                )
            )
        )

        health = (
            self.monitor.evaluate_health(
                current_metrics=(
                    metrics
                ),
                baseline_metrics=(
                    baseline_metrics
                ),
                rmse_degradation_threshold=(
                    rmse_degradation_threshold
                ),
                mape_threshold=(
                    mape_threshold
                )
            )
        )

        return {
            "model_id": (
                model_id
            ),
            "business_series_id": (
                business_series_id
            ),
            "model_type": (
                model_type
            ),
            "observations_available": (
                total
            ),
            "minimum_observations_required": (
                minimum_observations
            ),
            "sufficient_data": (
                True
            ),
            "metrics": (
                metrics
            ),
            "baseline_metrics": (
                baseline_metrics
            ),
            "health": (
                health
            ),
            "observations": (
                observations
            )
        }

    @staticmethod
    def _serialize_baseline(
        evaluation
    ) -> dict | None:

        if not evaluation:

            return None

        return {
            "evaluation_id": (
                evaluation.id
            ),
            "evaluation_type": (
                evaluation.evaluation_type
            ),
            "mae": (
                evaluation.mae
            ),
            "mse": (
                evaluation.mse
            ),
            "rmse": (
                evaluation.rmse
            ),
            "mape": (
                evaluation.mape
            ),
            "smape": (
                evaluation.smape
            ),
            "r2": (
                evaluation.r2
            )
        }