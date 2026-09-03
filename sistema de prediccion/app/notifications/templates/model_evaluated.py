from app.notifications.core.notification import Notification
from app.notifications.core.notification_type import NotificationCategory, NotificationPriority, NotificationType


def model_evaluated(*, evaluation_id: int, model_name: str, metrics: dict, is_winner: bool = False, recipient_role: str = "admin") -> Notification:
    title = "Nuevo modelo ganador" if is_winner else "Modelo evaluado"
    message = f"La evaluación de {model_name} finalizó."
    if is_winner:
        message += " Obtuvo el mejor desempeño en la comparación actual."
    return Notification(
        notification_type=NotificationType.MODEL_EVALUATED, category=NotificationCategory.MODEL,
        title=title, message=message, priority=NotificationPriority.MEDIUM if is_winner else NotificationPriority.INFO,
        recipient_role=recipient_role, entity_type="model_evaluation", entity_id=str(evaluation_id),
        payload={"model": model_name, "metrics": metrics, "is_winner": is_winner},
    )
