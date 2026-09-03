from app.notifications.core.notification import Notification
from app.notifications.core.notification_type import NotificationCategory, NotificationPriority, NotificationType


def demand_alert(*, entity_id: str, entity_name: str, predicted_demand: float, horizon_days: int, change_percent: float | None = None, recipient_role: str = "operator") -> Notification:
    return Notification(
        notification_type=NotificationType.DEMAND_ALERT, category=NotificationCategory.DEMAND,
        title="Cambio relevante en la demanda", message=f"Se proyecta una demanda de {predicted_demand:.2f} para {entity_name} en los próximos {horizon_days} días.",
        priority=NotificationPriority.MEDIUM, recipient_role=recipient_role, requires_action=True,
        suggested_action="Revisar inventario, capacidad y necesidades de compra para el horizonte proyectado.",
        entity_type="business_series", entity_id=entity_id,
        payload={"entity_name": entity_name, "predicted_demand": predicted_demand, "horizon_days": horizon_days, "change_percent": change_percent},
    )
