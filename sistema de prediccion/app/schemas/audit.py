from datetime import datetime
from typing import Any

from pydantic import BaseModel


class AuditLogResponse(BaseModel):

    id: int

    user_id: int | None

    action: str

    entity: str | None

    entity_id: str | None

    details: str | None

    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class AuditLogDetailResponse(
    BaseModel
):

    id: int

    user_id: int | None

    action: str

    entity: str | None

    entity_id: str | None

    details: (
        dict[str, Any]
        | list
        | str
        | None
    )

    created_at: datetime


class AuditSummaryResponse(
    BaseModel
):

    total_returned: int

    logs: list[
        AuditLogDetailResponse
    ]