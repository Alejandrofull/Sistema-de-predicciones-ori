from app.notifications.core.notification import Notification
from app.notifications.core.notification_type import NotificationCategory, NotificationPriority, NotificationType


def stock_alert(*, entity_id: str, entity_name: str, current_stock: float, projected_demand: float, horizon_days: int, recipient_role: str = "operator") -> Notification:
    deficit = max(projected_demand - current_stock, 0.0)
    priority = NotificationPriority.CRITICAL if current_stock <= 0 else NotificationPriority.HIGH
    return Notification(
        notification_type=NotificationType.STOCK_ALERT, category=NotificationCategory.INVENTORY,
        title="Riesgo de quiebre de stock", message=f"{entity_name} presenta riesgo de agotamiento dentro del horizonte de {horizon_days} días.",
        priority=priority, recipient_role=recipient_role, requires_action=True,
        suggested_action=f"Evaluar reabastecimiento de al menos {deficit:.2f} unidades, ajustando por stock de seguridad y lead time.",
        entity_type="business_series", entity_id=entity_id,
        payload={"entity_name": entity_name, "current_stock": current_stock, "projected_demand": projected_demand, "deficit_projected": deficit, "horizon_days": horizon_days},
    )
