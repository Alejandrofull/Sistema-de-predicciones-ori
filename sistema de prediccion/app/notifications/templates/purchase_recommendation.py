from app.notifications.core.notification import Notification
from app.notifications.core.notification_type import NotificationCategory, NotificationPriority, NotificationType


def purchase_recommendation(*, entity_id: str, entity_name: str, recommended_quantity: float, projected_demand: float, current_stock: float, lead_time_days: int | None = None, recipient_role: str = "operator") -> Notification:
    return Notification(
        notification_type=NotificationType.PURCHASE_RECOMMENDATION, category=NotificationCategory.INVENTORY,
        title="Compra de insumos sugerida", message=f"La proyección de demanda indica una necesidad de compra para {entity_name}.",
        priority=NotificationPriority.HIGH, recipient_role=recipient_role, requires_action=True,
        suggested_action=f"Evaluar la compra de aproximadamente {recommended_quantity:.2f} unidades.",
        entity_type="business_series", entity_id=entity_id,
        payload={"entity_name": entity_name, "recommended_quantity": recommended_quantity, "projected_demand": projected_demand, "current_stock": current_stock, "lead_time_days": lead_time_days},
    )
