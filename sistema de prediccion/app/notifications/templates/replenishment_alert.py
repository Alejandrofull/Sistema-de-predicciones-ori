from app.notifications.core.notification import Notification
from app.notifications.core.notification_type import NotificationCategory, NotificationPriority, NotificationType


def replenishment_alert(*, entity_id: str, entity_name: str, current_stock: float, reorder_point: float, recommended_quantity: float, recipient_role: str = "operator") -> Notification:
    return Notification(
        notification_type=NotificationType.REPLENISHMENT_ALERT, category=NotificationCategory.INVENTORY,
        title="Reabastecimiento recomendado", message=f"{entity_name} alcanzó o se aproxima al punto de reorden.",
        priority=NotificationPriority.HIGH, recipient_role=recipient_role, requires_action=True,
        suggested_action=f"Considerar un reabastecimiento aproximado de {recommended_quantity:.2f} unidades.",
        entity_type="business_series", entity_id=entity_id,
        payload={"entity_name": entity_name, "current_stock": current_stock, "reorder_point": reorder_point, "recommended_quantity": recommended_quantity},
    )
