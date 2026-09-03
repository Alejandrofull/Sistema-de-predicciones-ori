from app.notifications.core.notification import Notification
from app.notifications.core.notification_type import NotificationCategory, NotificationPriority, NotificationType


def retraining_completed(*, retraining_id: int, model_name: str, new_version: str, metrics: dict | None = None, recipient_role: str = "admin") -> Notification:
    return Notification(
        notification_type=NotificationType.RETRAINING_COMPLETED, category=NotificationCategory.RETRAINING,
        title="Reentrenamiento completado", message=f"{model_name} fue reentrenado correctamente. Nueva versión: {new_version}.",
        priority=NotificationPriority.MEDIUM, recipient_role=recipient_role, entity_type="retraining_run", entity_id=str(retraining_id),
        payload={"model": model_name, "new_version": new_version, "metrics": metrics or {}},
    )
