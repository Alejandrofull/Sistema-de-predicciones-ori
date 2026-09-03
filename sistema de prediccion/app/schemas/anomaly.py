from datetime import datetime
from typing import Any

from pydantic import BaseModel


class AnomalyResponse(BaseModel):

    id: int

    business_series_id: int | None

    model_id: int | None

    prediction_id: int | None

    prediction_result_id: int | None

    anomaly_type: str

    method: str

    observed_value: float | None

    expected_value: float | None

    deviation: float | None

    score: float | None

    severity: str

    status: str

    details: dict[
        str,
        Any
    ] | None

    detected_at: datetime

    resolved_at: datetime | None

    model_config = {
        "from_attributes": True
    }


class AnomalyDetectionResponse(
    BaseModel
):

    business_series_id: int | None

    observations_analyzed: int

    minimum_observations_required: int

    anomalies_detected: int

    anomalies_created: int

    anomalies_existing: int

    notifications_created: int

    anomalies: list[
        AnomalyResponse
    ]


class AnomalyStatusResponse(
    BaseModel
):

    id: int

    status: str

    resolved_at: datetime | None