from app.notifications.core.notification import Notification
from app.notifications.core.notification_type import NotificationCategory, NotificationPriority, NotificationType


def retraining_failed(*, retraining_id: int, model_name: str, error: str, recipient_role: str = "admin") -> Notification:
    return Notification(
        notification_type=NotificationType.RETRAINING_FAILED, category=NotificationCategory.RETRAINING,
        title="Reentrenamiento fallido", message=f"El reentrenamiento de {model_name} no pudo completarse.",
        priority=NotificationPriority.CRITICAL, recipient_role=recipient_role, requires_action=True,
        suggested_action="Revisar el error y mantener activa la última versión estable del modelo.",
        entity_type="retraining_run", entity_id=str(retraining_id), payload={"model": model_name, "error": error},
    )
