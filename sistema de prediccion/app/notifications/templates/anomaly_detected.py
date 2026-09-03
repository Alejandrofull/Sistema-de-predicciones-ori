from app.notifications.core.notification import Notification
from app.notifications.core.notification_type import NotificationCategory, NotificationPriority, NotificationType


def anomaly_detected(*, business_series_id: int | None, entity_name: str, detected_value: float, expected_value: float | None = None, anomaly_score: float | None = None, recipient_role: str = "operator") -> Notification:
    return Notification(
        notification_type=NotificationType.ANOMALY_DETECTED, category=NotificationCategory.MONITORING,
        title="Anomalía de demanda detectada", message=f"Se detectó un comportamiento atípico en {entity_name}.",
        priority=NotificationPriority.HIGH, recipient_role=recipient_role, requires_action=True,
        suggested_action="Validar el comportamiento de la demanda antes de tomar una decisión de abastecimiento.",
        entity_type="business_series", entity_id=str(business_series_id) if business_series_id is not None else None,
        payload={"entity_name": entity_name, "detected_value": detected_value, "expected_value": expected_value, "anomaly_score": anomaly_score},
    )
