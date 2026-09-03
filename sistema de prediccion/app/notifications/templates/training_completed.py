from app.notifications.core.notification import Notification
from app.notifications.core.notification_type import NotificationCategory, NotificationPriority, NotificationType


def training_completed(*, training_id: int, model_name: str, recipient_role: str = "admin", metrics: dict | None = None, duration_seconds: float | None = None) -> Notification:
    payload = {"training_id": training_id, "model": model_name, "metrics": metrics or {}, "duration_seconds": duration_seconds}
    return Notification(
        notification_type=NotificationType.TRAINING_COMPLETED, category=NotificationCategory.TRAINING,
        title="Entrenamiento completado", message=f"El entrenamiento de {model_name} finalizó correctamente.",
        priority=NotificationPriority.INFO, recipient_role=recipient_role, entity_type="training", entity_id=str(training_id), payload=payload,
    )
