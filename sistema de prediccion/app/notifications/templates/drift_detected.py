from app.notifications.core.notification import Notification
from app.notifications.core.notification_type import NotificationCategory, NotificationPriority, NotificationType


def drift_detected(*, model_version_id: int, model_name: str, drift_score: float, threshold: float, recipient_role: str = "admin") -> Notification:
    return Notification(
        notification_type=NotificationType.DRIFT_DETECTED, category=NotificationCategory.MONITORING,
        title="Drift detectado", message=f"Se detectó drift en {model_name}: {drift_score:.4f} supera el umbral {threshold:.4f}.",
        priority=NotificationPriority.HIGH, recipient_role=recipient_role, requires_action=True,
        suggested_action="Revisar desempeño y evaluar reentrenamiento del modelo.",
        entity_type="model_version", entity_id=str(model_version_id), payload={"drift_score": drift_score, "threshold": threshold},
    )
