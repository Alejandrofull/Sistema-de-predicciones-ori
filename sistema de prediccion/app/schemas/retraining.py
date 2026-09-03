from datetime import datetime
from typing import Any

from pydantic import (
    BaseModel,
    Field,
    model_validator,
)


SUPPORTED_TRIGGER_TYPES = {
    "metric_threshold",
    "rmse_degradation",
    "mape_threshold",
}


SUPPORTED_METRICS = {
    "mae",
    "mse",
    "rmse",
    "mape",
    "smape",
    "r2",
    "bias",
    "mean_absolute_error",
    "median_absolute_error",
    "max_absolute_error",
}


class RetrainingPolicyCreateRequest(
    BaseModel
):
    model_id: int = Field(
        ...,
        gt=0
    )

    trigger_type: str = Field(
        ...,
        min_length=1,
        max_length=50
    )

    metric_name: str | None = Field(
        default=None,
        max_length=50
    )

    threshold: float | None = None

    is_active: bool = True

    @model_validator(
        mode="after"
    )
    def validate_policy(
        self
    ):
        self.trigger_type = (
            self.trigger_type
            .strip()
            .lower()
        )

        if (
            self.trigger_type
            not in SUPPORTED_TRIGGER_TYPES
        ):
            raise ValueError(
                "trigger_type debe ser: "
                "metric_threshold, "
                "rmse_degradation o "
                "mape_threshold"
            )

        if self.metric_name:

            self.metric_name = (
                self.metric_name
                .strip()
                .lower()
            )

        if (
            self.trigger_type
            == "metric_threshold"
        ):

            if not self.metric_name:

                raise ValueError(
                    "metric_name es obligatorio "
                    "para metric_threshold"
                )

            if (
                self.metric_name
                not in SUPPORTED_METRICS
            ):

                raise ValueError(
                    "Métrica no soportada: "
                    f"{self.metric_name}"
                )

            if self.threshold is None:

                raise ValueError(
                    "threshold es obligatorio"
                )

        if (
            self.trigger_type
            == "rmse_degradation"
        ):

            self.metric_name = (
                "rmse_degradation"
            )

            if self.threshold is None:

                raise ValueError(
                    "threshold es obligatorio. "
                    "Ejemplo: 0.20 representa 20%."
                )

            if self.threshold < 0:

                raise ValueError(
                    "threshold no puede ser negativo"
                )

        if (
            self.trigger_type
            == "mape_threshold"
        ):

            self.metric_name = "mape"

            if self.threshold is None:

                raise ValueError(
                    "threshold es obligatorio. "
                    "Ejemplo: 20 representa 20%."
                )

            if self.threshold < 0:

                raise ValueError(
                    "threshold no puede ser negativo"
                )

        return self


class RetrainingPolicyUpdateRequest(
    RetrainingPolicyCreateRequest
):
    model_id: int | None = None


class RetrainingPolicyStatusRequest(
    BaseModel
):
    is_active: bool


class RetrainingPolicyResponse(
    BaseModel
):
    id: int

    model_id: int

    trigger_type: str

    metric_name: str | None

    threshold: float | None

    is_active: bool

    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class RetrainingPolicyDeleteResponse(
    BaseModel
):
    message: str


class RetrainingPolicyCheckItem(
    BaseModel
):
    policy_id: int

    trigger_type: str

    metric_name: str | None

    threshold: float | None

    current_value: float | None

    triggered: bool

    reason: str


class RetrainingCheckResponse(
    BaseModel
):
    model_id: int

    business_series_id: int | None

    sufficient_data: bool

    should_retrain: bool

    triggered_policy_ids: list[int]

    checks: list[
        RetrainingPolicyCheckItem
    ]

    performance: dict[
        str,
        Any
    ]


class RetrainingExecuteRequest(
    BaseModel
):
    dataset_id: int | None = Field(
        default=None,
        gt=0
    )

    reason: str | None = Field(
        default=None,
        max_length=2000
    )


class RetrainingRunResponse(
    BaseModel
):
    id: int

    model_id: int

    previous_version_id: int | None

    new_version_id: int | None

    dataset_id: int

    trigger_type: str

    reason: str | None

    status: str

    started_at: datetime | None

    finished_at: datetime | None

    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class RetrainingExecutionResponse(
    BaseModel
):
    run: RetrainingRunResponse

    model_id: int

    previous_version_id: int | None

    new_version_id: int

    model_type: str

    dataset_id: int

    business_series_id: int | None

    metrics: dict[
        str,
        Any
    ]

    activation_required: bool

    message: str


class RetrainingCheckAndRunResponse(
    BaseModel
):
    checked: bool

    triggered: bool

    check: RetrainingCheckResponse

    execution: (
        RetrainingExecutionResponse
        | None
    )