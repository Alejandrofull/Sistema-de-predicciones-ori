from __future__ import annotations

from datetime import (
    date,
    datetime,
    time,
    timezone,
)

from sqlalchemy import (
    func,
    select,
)

from sqlalchemy.orm import Session

from app.models.anomaly import (
    Anomaly,
)

from app.models.business_series import (
    BusinessSeries,
)

from app.models.model import (
    MLModel,
)

from app.models.model_evaluations import (
    ModelEvaluation,
)

from app.models.prediction import (
    Prediction,
    PredictionResult,
)

from app.models.retraining_runs import (
    RetrainingRun,
)

from app.models.training import (
    Training,
)


class KPIService:

    # ==========================================
    # CONFIGURACIÓN
    # ==========================================

    RMSE_DEGRADATION_THRESHOLD = 20.0

    # ==========================================
    # KPI TÉCNICO POR MODELO
    # ==========================================

    def get_model_technical_kpis(
        self,
        db: Session,
        model_id: int
    ) -> dict:

        model = db.get(
            MLModel,
            model_id
        )

        if not model:

            raise ValueError(
                "Modelo no encontrado"
            )

        evaluations = list(
            db.scalars(
                select(
                    ModelEvaluation
                )
                .where(
                    ModelEvaluation.model_id
                    == model.id
                )
                .order_by(
                    ModelEvaluation.evaluated_at.desc(),
                    ModelEvaluation.id.desc()
                )
                .limit(2)
            ).all()
        )

        latest_evaluation = (
            evaluations[0]
            if evaluations
            else None
        )

        previous_evaluation = (
            evaluations[1]
            if len(
                evaluations
            ) > 1
            else None
        )

        previous_rmse = (
            self._to_float(
                previous_evaluation.rmse
            )
            if previous_evaluation
            else None
        )

        current_rmse = (
            self._to_float(
                latest_evaluation.rmse
            )
            if latest_evaluation
            else None
        )

        (
            rmse_change_absolute,
            rmse_change_percent,
            performance_status
        ) = self._calculate_rmse_change(
            current_rmse=(
                current_rmse
            ),
            previous_rmse=(
                previous_rmse
            )
        )

        total_predictions = (
            db.scalar(
                select(
                    func.count(
                        Prediction.id
                    )
                )
                .where(
                    Prediction.model_id
                    == model.id
                )
            )
            or 0
        )

        predictions_with_actual = (
            db.scalar(
                select(
                    func.count(
                        PredictionResult.id
                    )
                )
                .join(
                    Prediction,
                    Prediction.id
                    == PredictionResult.prediction_id
                )
                .where(
                    Prediction.model_id
                    == model.id,
                    PredictionResult.actual_value
                    .is_not(None)
                )
            )
            or 0
        )

        active_anomalies = (
            db.scalar(
                select(
                    func.count(
                        Anomaly.id
                    )
                )
                .where(
                    Anomaly.model_id
                    == model.id,
                    Anomaly.status
                    == "open"
                )
            )
            or 0
        )

        critical_anomalies = (
            db.scalar(
                select(
                    func.count(
                        Anomaly.id
                    )
                )
                .where(
                    Anomaly.model_id
                    == model.id,
                    Anomaly.status
                    == "open",
                    Anomaly.severity
                    == "critical"
                )
            )
            or 0
        )

        total_retraining_runs = (
            db.scalar(
                select(
                    func.count(
                        RetrainingRun.id
                    )
                )
                .where(
                    RetrainingRun.model_id
                    == model.id
                )
            )
            or 0
        )

        last_training_at = db.scalar(
            select(
                func.max(
                    Training.finished_at
                )
            )
            .where(
                Training.model_id
                == model.id,
                Training.status
                == "completed"
            )
        )

        last_retraining_at = db.scalar(
            select(
                func.max(
                    RetrainingRun.finished_at
                )
            )
            .where(
                RetrainingRun.model_id
                == model.id,
                RetrainingRun.status
                == "completed"
            )
        )

        return {
            "model": {
                "model_id": (
                    model.id
                ),
                "business_series_id": (
                    model.business_series_id
                ),
                "model_type": (
                    model.model_type
                ),
                "version": (
                    model.version
                ),
                "active": (
                    model.active
                ),
                "metric_value": (
                    self._to_float(
                        model.metric_value
                    )
                )
            },
            "evaluation": {
                "evaluation_id": (
                    latest_evaluation.id
                    if latest_evaluation
                    else None
                ),
                "model_version_id": (
                    latest_evaluation
                    .model_version_id
                    if latest_evaluation
                    else None
                ),
                "evaluated_at": (
                    latest_evaluation
                    .evaluated_at
                    if latest_evaluation
                    else None
                ),
                "evaluation_type": (
                    latest_evaluation
                    .evaluation_type
                    if latest_evaluation
                    else None
                )
            },
            "metrics": {
                "mae": (
                    self._evaluation_metric(
                        latest_evaluation,
                        "mae"
                    )
                ),
                "mse": (
                    self._evaluation_metric(
                        latest_evaluation,
                        "mse"
                    )
                ),
                "rmse": (
                    current_rmse
                ),
                "mape": (
                    self._evaluation_metric(
                        latest_evaluation,
                        "mape"
                    )
                ),
                "smape": (
                    self._evaluation_metric(
                        latest_evaluation,
                        "smape"
                    )
                ),
                "r2": (
                    self._evaluation_metric(
                        latest_evaluation,
                        "r2"
                    )
                )
            },
            "previous_rmse": (
                previous_rmse
            ),
            "rmse_change_absolute": (
                rmse_change_absolute
            ),
            "rmse_change_percent": (
                rmse_change_percent
            ),
            "performance_status": (
                performance_status
            ),
            "total_predictions": int(
                total_predictions
            ),
            "predictions_with_actual": int(
                predictions_with_actual
            ),
            "active_anomalies": int(
                active_anomalies
            ),
            "critical_anomalies": int(
                critical_anomalies
            ),
            "total_retraining_runs": int(
                total_retraining_runs
            ),
            "last_training_at": (
                last_training_at
            ),
            "last_retraining_at": (
                last_retraining_at
            )
        }

    # ==========================================
    # DASHBOARD TÉCNICO
    # ==========================================

    def get_technical_dashboard(
        self,
        db: Session
    ) -> dict:

        models = list(
            db.scalars(
                select(
                    MLModel
                )
                .order_by(
                    MLModel.id.asc()
                )
            ).all()
        )

        model_kpis = []

        degraded_models = 0

        evaluated_models = 0

        for model in models:

            model_data = (
                self.get_model_technical_kpis(
                    db=db,
                    model_id=model.id
                )
            )

            if (
                model_data[
                    "evaluation"
                ][
                    "evaluation_id"
                ]
                is not None
            ):
                evaluated_models += 1

            if (
                model_data[
                    "performance_status"
                ]
                == "degraded"
            ):
                degraded_models += 1

            model_kpis.append(
                model_data
            )

        active_anomalies = (
            db.scalar(
                select(
                    func.count(
                        Anomaly.id
                    )
                )
                .where(
                    Anomaly.status
                    == "open"
                )
            )
            or 0
        )

        critical_anomalies = (
            db.scalar(
                select(
                    func.count(
                        Anomaly.id
                    )
                )
                .where(
                    Anomaly.status
                    == "open",
                    Anomaly.severity
                    == "critical"
                )
            )
            or 0
        )

        active_models = sum(
            1
            for model
            in models
            if model.active
        )

        return {
            "total_models": (
                len(
                    models
                )
            ),
            "active_models": (
                active_models
            ),
            "evaluated_models": (
                evaluated_models
            ),
            "models_with_degraded_performance": (
                degraded_models
            ),
            "active_anomalies": int(
                active_anomalies
            ),
            "critical_anomalies": int(
                critical_anomalies
            ),
            "models": (
                model_kpis
            )
        }

    # ==========================================
    # DASHBOARD OPERACIONAL
    # ==========================================

    def get_operational_kpis(
        self,
        db: Session,
        start_date: date | None = None,
        end_date: date | None = None,
        business_series_id: int | None = None
    ) -> dict:

        start_datetime = (
            self._start_of_day(
                start_date
            )
            if start_date
            else None
        )

        end_datetime = (
            self._end_of_day(
                end_date
            )
            if end_date
            else None
        )

        series_statement = (
            select(
                BusinessSeries
            )
            .where(
                BusinessSeries.is_active.is_(
                    True
                )
            )
            .order_by(
                BusinessSeries.id.asc()
            )
        )

        if business_series_id is not None:

            series_statement = (
                series_statement.where(
                    BusinessSeries.id
                    == business_series_id
                )
            )

        business_series = list(
            db.scalars(
                series_statement
            ).all()
        )

        monitored_series = len(
            business_series
        )

        series_kpis = []

        for series in business_series:

            series_data = (
                self._get_operational_series_kpi(
                    db=db,
                    business_series=series,
                    start_datetime=(
                        start_datetime
                    ),
                    end_datetime=(
                        end_datetime
                    )
                )
            )

            if (
                series_data[
                    "forecast_records"
                ] > 0
            ):

                series_kpis.append(
                    series_data
                )

        prediction_run_statement = (
            select(
                func.count(
                    Prediction.id
                )
            )
        )

        if start_datetime is not None:

            prediction_run_statement = (
                prediction_run_statement
                .where(
                    Prediction.created_at
                    >= start_datetime
                )
            )

        if end_datetime is not None:

            prediction_run_statement = (
                prediction_run_statement
                .where(
                    Prediction.created_at
                    <= end_datetime
                )
            )

        if business_series_id is not None:

            prediction_run_statement = (
                prediction_run_statement
                .where(
                    Prediction.business_series_id
                    == business_series_id
                )
            )

        total_prediction_runs = (
            db.scalar(
                prediction_run_statement
            )
            or 0
        )

        result_statement = (
            select(
                PredictionResult
            )
            .join(
                Prediction,
                Prediction.id
                == PredictionResult.prediction_id
            )
        )

        if start_date is not None:

            result_statement = (
                result_statement.where(
                    PredictionResult.prediction_date
                    >= start_date
                )
            )

        if end_date is not None:

            result_statement = (
                result_statement.where(
                    PredictionResult.prediction_date
                    <= end_date
                )
            )

        if business_series_id is not None:

            result_statement = (
                result_statement.where(
                    Prediction.business_series_id
                    == business_series_id
                )
            )

        results = list(
            db.scalars(
                result_statement
            ).all()
        )

        projected_values = [
            float(
                result.predicted_value
            )
            for result
            in results
            if (
                result.predicted_value
                is not None
            )
        ]

        actual_values = [
            float(
                result.actual_value
            )
            for result
            in results
            if (
                result.actual_value
                is not None
            )
        ]

        absolute_errors = [
            abs(
                float(
                    result.actual_value
                )
                -
                float(
                    result.predicted_value
                )
            )
            for result
            in results
            if (
                result.actual_value
                is not None
                and result.predicted_value
                is not None
            )
        ]

        anomaly_statement = (
            select(
                Anomaly
            )
            .where(
                Anomaly.status
                == "open"
            )
        )

        if business_series_id is not None:

            anomaly_statement = (
                anomaly_statement
                .where(
                    Anomaly.business_series_id
                    == business_series_id
                )
            )

        if start_datetime is not None:

            anomaly_statement = (
                anomaly_statement.where(
                    Anomaly.detected_at
                    >= start_datetime
                )
            )

        if end_datetime is not None:

            anomaly_statement = (
                anomaly_statement.where(
                    Anomaly.detected_at
                    <= end_datetime
                )
            )

        anomalies = list(
            db.scalars(
                anomaly_statement
            ).all()
        )

        active_anomalies = len(
            anomalies
        )

        critical_anomalies = sum(
            1
            for anomaly
            in anomalies
            if anomaly.severity
            == "critical"
        )

        highest_demand_series = None

        if series_kpis:

            highest_demand_series = max(
                series_kpis,
                key=lambda item: (
                    item[
                        "total_forecast"
                    ]
                )
            )

        return {
            "start_date": (
                start_date
            ),
            "end_date": (
                end_date
            ),
            "monitored_series": (
                monitored_series
            ),
            "series_with_predictions": (
                len(
                    series_kpis
                )
            ),
            "total_prediction_runs": int(
                total_prediction_runs
            ),
            "total_forecast_records": (
                len(
                    projected_values
                )
            ),
            "projected_demand_total": (
                self._sum(
                    projected_values
                )
            ),
            "projected_demand_average": (
                self._average(
                    projected_values
                )
            ),
            "projected_demand_minimum": (
                min(
                    projected_values
                )
                if projected_values
                else None
            ),
            "projected_demand_maximum": (
                max(
                    projected_values
                )
                if projected_values
                else None
            ),
            "actual_demand_total": (
                self._sum(
                    actual_values
                )
                if actual_values
                else None
            ),
            "actual_demand_average": (
                self._average(
                    actual_values
                )
                if actual_values
                else None
            ),
            "forecast_error_absolute_total": (
                self._sum(
                    absolute_errors
                )
                if absolute_errors
                else None
            ),
            "active_anomalies": (
                active_anomalies
            ),
            "critical_anomalies": (
                critical_anomalies
            ),
            "highest_demand_series": (
                highest_demand_series
            ),
            "series": (
                sorted(
                    series_kpis,
                    key=lambda item: (
                        item[
                            "total_forecast"
                        ]
                    ),
                    reverse=True
                )
            )
        }

    # ==========================================
    # KPI OPERACIONAL POR SERIE
    # ==========================================

    def _get_operational_series_kpi(
        self,
        db: Session,
        business_series,
        start_datetime: datetime | None,
        end_datetime: datetime | None
    ) -> dict:

        statement = (
            select(
                PredictionResult
            )
            .join(
                Prediction,
                Prediction.id
                == PredictionResult.prediction_id
            )
            .where(
                Prediction.business_series_id
                == business_series.id
            )
            .order_by(
                PredictionResult.prediction_date.asc()
            )
        )

        if start_datetime is not None:

            statement = statement.where(
                PredictionResult.prediction_date
                >= start_datetime.date()
            )

        if end_datetime is not None:

            statement = statement.where(
                PredictionResult.prediction_date
                <= end_datetime.date()
            )

        results = list(
            db.scalars(
                statement
            ).all()
        )

        values = [
            float(
                result.predicted_value
            )
            for result
            in results
            if result.predicted_value
            is not None
        ]

        prediction_dates = [
            result.prediction_date
            for result
            in results
            if result.prediction_date
            is not None
        ]

        active_anomalies = (
            db.scalar(
                select(
                    func.count(
                        Anomaly.id
                    )
                )
                .where(
                    Anomaly.business_series_id
                    == business_series.id,
                    Anomaly.status
                    == "open"
                )
            )
            or 0
        )

        if not values:

            return {
                "business_series_id": (
                    business_series.id
                ),
                "series_name": (
                    business_series.name
                    or business_series
                    .external_entity_id
                ),
                "external_entity_id": (
                    business_series
                    .external_entity_id
                ),
                "total_forecast": 0.0,
                "average_forecast": 0.0,
                "minimum_forecast": 0.0,
                "maximum_forecast": 0.0,
                "forecast_records": 0,
                "first_prediction_date": None,
                "last_prediction_date": None,
                "active_anomalies": int(
                    active_anomalies
                )
            }

        return {
            "business_series_id": (
                business_series.id
            ),
            "series_name": (
                business_series.name
                or business_series
                .external_entity_id
            ),
            "external_entity_id": (
                business_series
                .external_entity_id
            ),
            "total_forecast": (
                self._sum(
                    values
                )
            ),
            "average_forecast": (
                self._average(
                    values
                )
            ),
            "minimum_forecast": (
                min(
                    values
                )
            ),
            "maximum_forecast": (
                max(
                    values
                )
            ),
            "forecast_records": (
                len(
                    values
                )
            ),
            "first_prediction_date": (
                min(
                    prediction_dates
                )
                if prediction_dates
                else None
            ),
            "last_prediction_date": (
                max(
                    prediction_dates
                )
                if prediction_dates
                else None
            ),
            "active_anomalies": int(
                active_anomalies
            )
        }

    # ==========================================
    # DEGRADACIÓN RMSE
    # ==========================================

    def _calculate_rmse_change(
        self,
        current_rmse: float | None,
        previous_rmse: float | None
    ) -> tuple[
        float | None,
        float | None,
        str
    ]:

        if current_rmse is None:

            return (
                None,
                None,
                "not_evaluated"
            )

        if previous_rmse is None:

            return (
                None,
                None,
                "baseline"
            )

        difference = (
            current_rmse
            -
            previous_rmse
        )

        if previous_rmse == 0:

            percent = None

            status = (
                "degraded"
                if current_rmse > 0
                else "stable"
            )

            return (
                float(
                    difference
                ),
                percent,
                status
            )

        percent = (
            difference
            /
            previous_rmse
            *
            100.0
        )

        if (
            percent
            >= self.RMSE_DEGRADATION_THRESHOLD
        ):

            status = "degraded"

        elif percent > 0:

            status = "warning"

        elif percent < 0:

            status = "improved"

        else:

            status = "stable"

        return (
            float(
                difference
            ),
            float(
                percent
            ),
            status
        )

    # ==========================================
    # HELPERS
    # ==========================================

    @staticmethod
    def _evaluation_metric(
        evaluation,
        field_name: str
    ) -> float | None:

        if evaluation is None:
            return None

        return KPIService._to_float(
            getattr(
                evaluation,
                field_name,
                None
            )
        )

    @staticmethod
    def _to_float(
        value
    ) -> float | None:

        if value is None:
            return None

        return float(
            value
        )

    @staticmethod
    def _sum(
        values: list[float]
    ) -> float:

        if not values:
            return 0.0

        return float(
            sum(
                values
            )
        )

    @staticmethod
    def _average(
        values: list[float]
    ) -> float:

        if not values:
            return 0.0

        return float(
            sum(
                values
            )
            /
            len(
                values
            )
        )

    @staticmethod
    def _start_of_day(
        value: date
    ) -> datetime:

        return datetime.combine(
            value,
            time.min,
            tzinfo=timezone.utc
        )

    @staticmethod
    def _end_of_day(
        value: date
    ) -> datetime:

        return datetime.combine(
            value,
            time.max,
            tzinfo=timezone.utc
        )