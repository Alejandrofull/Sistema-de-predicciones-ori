from app.notifications.core.notification import Notification
from app.notifications.core.notification_type import NotificationCategory, NotificationPriority, NotificationType


def model_activated(*, model_id: int, model_name: str, version: str, previous_model: str | None = None, recipient_role: str = "admin") -> Notification:
    msg = f"{model_name} {version} fue activado como modelo operativo."
    if previous_model:
        msg += f" Reemplaza a {previous_model}."
    return Notification(
        notification_type=NotificationType.MODEL_ACTIVATED, category=NotificationCategory.MODEL,
        title="Modelo operativo actualizado", message=msg, priority=NotificationPriority.MEDIUM,
        recipient_role=recipient_role, entity_type="model", entity_id=str(model_id),
        payload={"model": model_name, "version": version, "previous_model": previous_model},
    )
