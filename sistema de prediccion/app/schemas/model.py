from datetime import datetime
from typing import Any

from pydantic import BaseModel


class MLModelResponse(BaseModel):

    id: int

    business_series_id: int | None

    name: str

    model_type: str

    version: str | None

    metric_value: float | None

    active: bool

    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class ModelVersionResponse(BaseModel):

    id: int

    model_id: int

    version_number: int

    parameters: dict[
        str,
        Any
    ] | None

    feature_config: dict[
        str,
        Any
    ] | None

    artifact_path: str | None

    is_active: bool

    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class ModelEvaluationResponse(BaseModel):

    id: int

    model_id: int

    model_version_id: int | None

    training_id: int | None

    dataset_id: int

    evaluation_type: str

    mae: float | None

    mse: float | None

    rmse: float | None

    mape: float | None

    smape: float | None

    r2: float | None

    training_time_seconds: float | None

    prediction_time_seconds: float | None

    score: float | None

    ranking_position: int | None

    is_best_model: bool

    evaluation_config: dict[
        str,
        Any
    ] | None

    notes: str | None

    evaluated_at: datetime

    model_config = {
        "from_attributes": True
    }


class ModelActivationResponse(BaseModel):

    model_id: int

    model_version_id: int

    business_series_id: int | None

    model_type: str

    active: bool

    message: str