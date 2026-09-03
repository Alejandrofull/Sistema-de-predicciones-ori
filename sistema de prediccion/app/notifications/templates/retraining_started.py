from app.notifications.core.notification import Notification
from app.notifications.core.notification_type import NotificationCategory, NotificationPriority, NotificationType


def retraining_started(*, retraining_id: int, model_name: str, reason: str, trigger_type: str, recipient_role: str = "admin") -> Notification:
    return Notification(
        notification_type=NotificationType.RETRAINING_STARTED, category=NotificationCategory.RETRAINING,
        title="Reentrenamiento iniciado", message=f"Se inició el reentrenamiento de {model_name}.",
        priority=NotificationPriority.INFO, recipient_role=recipient_role, entity_type="retraining_run", entity_id=str(retraining_id),
        payload={"model": model_name, "reason": reason, "trigger_type": trigger_type},
    )
