from app.notifications.core.notification import Notification
from app.notifications.core.notification_type import NotificationCategory, NotificationPriority, NotificationType


def overstock_alert(*, entity_id: str, entity_name: str, current_stock: float, projected_demand: float, excess_quantity: float, recipient_role: str = "operator") -> Notification:
    return Notification(
        notification_type=NotificationType.OVERSTOCK_ALERT, category=NotificationCategory.INVENTORY,
        title="Posible sobrestock", message=f"El inventario de {entity_name} supera la demanda proyectada de forma significativa.",
        priority=NotificationPriority.MEDIUM, recipient_role=recipient_role, requires_action=True,
        suggested_action="Revisar próximas compras, promociones o redistribución de inventario.",
        entity_type="business_series", entity_id=entity_id,
        payload={"entity_name": entity_name, "current_stock": current_stock, "projected_demand": projected_demand, "excess_quantity": excess_quantity},
    )
