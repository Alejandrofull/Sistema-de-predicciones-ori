from app.notifications.core.notification import Notification
from app.notifications.core.notification_type import NotificationCategory, NotificationPriority, NotificationType


def training_failed(*, training_id: int, model_name: str, error: str, recipient_role: str = "admin") -> Notification:
    return Notification(
        notification_type=NotificationType.TRAINING_FAILED, category=NotificationCategory.TRAINING,
        title="Entrenamiento fallido", message=f"El entrenamiento de {model_name} no pudo completarse.",
        priority=NotificationPriority.HIGH, recipient_role=recipient_role, requires_action=True,
        suggested_action="Revisar el error del entrenamiento y decidir si debe reintentarse.",
        entity_type="training", entity_id=str(training_id), payload={"model": model_name, "error": error},
    )
