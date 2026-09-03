from datetime import date
from typing import Any

from pydantic import (
    BaseModel,
    Field,
)


class PerformanceObservationResponse(
    BaseModel
):

    prediction_result_id: int

    prediction_date: date

    predicted_value: float

    actual_value: float

    error: float

    absolute_error: float


class PerformanceMetricsResponse(
    BaseModel
):

    samples: int

    mae: float

    mse: float

    rmse: float

    mape: float | None

    smape: float

    r2: float | None

    bias: float

    mean_absolute_error: float

    median_absolute_error: float

    max_absolute_error: float

    under_predictions: int

    over_predictions: int

    exact_predictions: int

    under_prediction_percentage: float

    over_prediction_percentage: float


class ModelHealthResponse(
    BaseModel
):

    status: str

    retraining_recommended: bool

    rmse_degradation: float | None

    bias_direction: str | None

    warnings: list[
        dict[
            str,
            Any
        ]
    ]


class ProductionPerformanceResponse(
    BaseModel
):

    model_id: int | None

    business_series_id: int | None

    model_type: str | None

    observations_available: int

    minimum_observations_required: int

    sufficient_data: bool

    metrics: (
        PerformanceMetricsResponse
        | None
    )

    baseline_metrics: dict[
        str,
        Any
    ] | None

    health: (
        ModelHealthResponse
        | None
    )

    observations: list[
        PerformanceObservationResponse
    ]


class PerformanceQueryConfig(
    BaseModel
):

    limit: int = Field(
        default=100,
        ge=1,
        le=5000
    )

    minimum_observations: int = Field(
        default=5,
        ge=2,
        le=1000
    )

    rmse_degradation_threshold: float = Field(
        default=0.20,
        ge=0.0,
        le=10.0
    )

    mape_threshold: float = Field(
        default=20.0,
        ge=0.0,
        le=1000.0
    )