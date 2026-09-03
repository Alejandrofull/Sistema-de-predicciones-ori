from datetime import datetime
from typing import Any

from pydantic import BaseModel


class NotificationResponse(BaseModel):

    id: int

    user_id: int | None

    recipient_role: str | None

    category: str

    notification_type: str

    title: str

    message: str

    priority: str

    requires_action: bool

    suggested_action: str | None

    entity_type: str | None

    entity_id: str | None

    payload: dict[
        str,
        Any
    ] | None

    is_read: bool

    read_at: datetime | None

    acknowledged: bool

    acknowledged_at: datetime | None

    created_at: datetime

    model_config = {
        "from_attributes": True
    }