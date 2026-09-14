from datetime import datetime
from typing import Any

from pydantic import (
    BaseModel,
    Field,
    field_validator,
)


SUPPORTED_MODELS = {
    "arima",
    "random_forest",
    "xgboost",
    "hybrid",
}


class TrainingRequest(BaseModel):

    dataset_id: int = Field(
        ...,
        gt=0
    )

    date_column: str | None = None

    target_column: str | None = None

    model_names: list[str] = Field(
        default_factory=lambda: [
            "arima",
            "random_forest",
            "xgboost",
            "hybrid",
        ]
    )

    test_ratio: float = Field(
        default=0.20,
        ge=0.05,
        le=0.40
    )

    allow_all_users: bool = False

    @field_validator(
        "model_names"
    )
    @classmethod
    def validate_model_names(
        cls,
        values: list[str]
    ) -> list[str]:

        normalized = []

        for value in values:

            model_name = (
                value
                .lower()
                .strip()
            )

            if model_name not in (
                SUPPORTED_MODELS
            ):

                raise ValueError(
                    "Modelo no soportado: "
                    f"{model_name}"
                )

            if model_name not in normalized:

                normalized.append(
                    model_name
                )

        if not normalized:

            raise ValueError(
                "Debe seleccionar "
                "al menos un modelo"
            )

        return normalized


class TrainingModelSelection(BaseModel):

    metric: str

    source: str

    value: float


class TrainingModelBacktesting(BaseModel):

    strategy: str | None = None

    horizon: int | None = None

    step: int | None = None

    successful_folds: int | None = None

    failed_folds: int | None = None

    mean_metrics: dict[str, Any] | None = None

    std_metrics: dict[str, Any] | None = None


class TrainingModelResult(BaseModel):

    training_id: int

    model_id: int

    model_version_id: int

    model_name: str

    model_type: str

    version_number: int

    artifact_path: str

    metrics: dict[
        str,
        Any
    ]

    backtesting: TrainingModelBacktesting | None = None

    backtesting_error: str | None = None

    selection: TrainingModelSelection

    ranking_position: int

    is_best_model: bool

    training_time_seconds: float


class TrainingRunResponse(BaseModel):

    dataset_id: int

    business_series_id: int | None

    winner: str

    winner_model_id: int

    ranking: list[str]

    ranking_metric: str

    winner_selection_rmse: float

    results: list[
        TrainingModelResult
    ]

    errors: dict[
        str,
        str
    ]


class TrainingResponse(BaseModel):

    id: int

    dataset_id: int

    model_id: int | None

    status: str

    started_at: datetime | None

    finished_at: datetime | None

    created_at: datetime

    model_config = {
        "from_attributes": True
    }