from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.notifications.core.notification_type import (
    NotificationCategory,
    NotificationPriority,
    NotificationType,
)


@dataclass(slots=True)
class Notification:
    notification_type: NotificationType
    category: NotificationCategory
    title: str
    message: str
    priority: NotificationPriority = NotificationPriority.INFO
    recipient_user_id: int | None = None
    recipient_role: str | None = None
    requires_action: bool = False
    suggested_action: str | None = None
    entity_type: str | None = None
    entity_id: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if self.recipient_user_id is None and self.recipient_role is None:
            raise ValueError("La notificación debe tener recipient_user_id o recipient_role")
        if self.requires_action and not self.suggested_action:
            raise ValueError("requires_action=True requiere suggested_action")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "notification_type": self.notification_type.value,
            "category": self.category.value,
            "title": self.title,
            "message": self.message,
            "priority": self.priority.value,
            "recipient_user_id": self.recipient_user_id,
            "recipient_role": self.recipient_role,
            "requires_action": self.requires_action,
            "suggested_action": self.suggested_action,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "payload": self.payload,
            "created_at": self.created_at.isoformat(),
        }
