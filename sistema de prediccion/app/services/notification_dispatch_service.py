from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.repositories.push_subscription_repository import PushSubscriptionRepository
from app.schemas.notification import NotificationResponse
from app.services.authorization_service import AuthorizationService
from app.services.push_service import PushService
from app.websockets.connection_manager import manager


class NotificationDispatchService:

    @staticmethod
    def _resolve_recipient_ids(db: Session, notification: Notification) -> list[int]:

        if notification.user_id is not None:
            return [notification.user_id]

        if notification.recipient_role is not None:
            # Ajusta esto al método real de tu AuthorizationService
            # para obtener los ids de usuarios que tienen ese rol.
            return AuthorizationService.get_user_ids_by_role(
                db=db, role=notification.recipient_role
            )

        return []

    @classmethod
    async def dispatch(cls, db: Session, notification: Notification) -> None:

        recipient_ids = cls._resolve_recipient_ids(db, notification)

        if not recipient_ids:
            return

        payload = {
            "type": "notification.new",
            "data": NotificationResponse.model_validate(notification).model_dump(mode="json"),
        }

        await manager.send_to_users(recipient_ids, payload)

        subscriptions = PushSubscriptionRepository.get_for_users(db, recipient_ids)

        PushService.send_to_subscriptions(
            db=db,
            subscriptions=subscriptions,
            title=notification.title,
            body=notification.message,
            data={
                "notification_id": notification.id,
                "category": notification.category,
            },
        )