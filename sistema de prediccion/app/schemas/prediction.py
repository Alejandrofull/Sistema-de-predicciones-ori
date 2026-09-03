from datetime import (
    date,
    datetime,
)

from typing import Any

from pydantic import (
    BaseModel,
    Field,
)


class PredictionRequest(BaseModel):

    horizon: int = Field(
        default=7,
        ge=1,
        le=365,
        description=(
            "Cantidad de periodos futuros "
            "que se desean predecir"
        )
    )

    dataset_id: int | None = Field(
        default=None,
        gt=0
    )

    business_series_id: int | None = Field(
        default=None,
        gt=0
    )

    clip_negative: bool = Field(
        default=True,
        description=(
            "Convierte predicciones negativas "
            "de demanda a cero"
        )
    )

    future_features: list[
        dict[str, Any]
    ] | None = Field(
        default=None,
        description=(
            "Variables externas futuras. "
            "Debe contener un registro por "
            "periodo cuando el modelo utilice "
            "features que no puedan calcularse "
            "automáticamente."
        )
    )


class PredictionResultResponse(
    BaseModel
):

    id: int

    prediction_id: int

    prediction_date: date

    predicted_value: float

    actual_value: float | None

    lower_bound: float | None

    upper_bound: float | None

    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class PredictionResponse(
    BaseModel
):

    id: int

    user_id: int | None

    model_id: int

    model_version_id: int | None

    dataset_id: int | None

    business_series_id: int | None

    horizon: int

    start_date: date

    end_date: date

    status: str

    created_at: datetime

    completed_at: datetime | None

    model_config = {
        "from_attributes": True
    }


class PredictionRunResponse(
    BaseModel
):

    prediction: PredictionResponse

    model_type: str

    model_version: int

    results: list[
        PredictionResultResponse
    ]


class ActualValueUpdate(
    BaseModel
):

    actual_value: float