from __future__ import annotations

from datetime import (
    date,
    datetime,
)

from pydantic import BaseModel


class TechnicalMetricValues(BaseModel):

    mae: float | None = None
    mse: float | None = None
    rmse: float | None = None
    mape: float | None = None
    smape: float | None = None
    r2: float | None = None


class TechnicalModelInfo(BaseModel):

    model_id: int

    business_series_id: int | None

    model_type: str

    version: str | None

    active: bool

    metric_value: float | None


class TechnicalEvaluationInfo(BaseModel):

    evaluation_id: int | None

    model_version_id: int | None

    evaluated_at: datetime | None

    evaluation_type: str | None


class TechnicalKPIResponse(BaseModel):

    model: TechnicalModelInfo

    evaluation: TechnicalEvaluationInfo

    metrics: TechnicalMetricValues

    previous_rmse: float | None

    rmse_change_absolute: float | None

    rmse_change_percent: float | None

    performance_status: str

    total_predictions: int

    predictions_with_actual: int

    active_anomalies: int

    critical_anomalies: int

    total_retraining_runs: int

    last_training_at: datetime | None

    last_retraining_at: datetime | None


class TechnicalDashboardResponse(BaseModel):

    total_models: int

    active_models: int

    evaluated_models: int

    models_with_degraded_performance: int

    active_anomalies: int

    critical_anomalies: int

    models: list[
        TechnicalKPIResponse
    ]


class OperationalSeriesKPI(BaseModel):

    business_series_id: int

    series_name: str

    external_entity_id: str

    total_forecast: float

    average_forecast: float

    minimum_forecast: float

    maximum_forecast: float

    forecast_records: int

    first_prediction_date: date | None

    last_prediction_date: date | None

    active_anomalies: int


class OperationalKPIResponse(BaseModel):

    start_date: date | None

    end_date: date | None

    monitored_series: int

    series_with_predictions: int

    total_prediction_runs: int

    total_forecast_records: int

    projected_demand_total: float

    projected_demand_average: float

    projected_demand_minimum: float | None

    projected_demand_maximum: float | None

    actual_demand_total: float | None

    actual_demand_average: float | None

    forecast_error_absolute_total: float | None

    active_anomalies: int

    critical_anomalies: int

    highest_demand_series: (
        OperationalSeriesKPI
        | None
    )

    series: list[
        OperationalSeriesKPI
    ]