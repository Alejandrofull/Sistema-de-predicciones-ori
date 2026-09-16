import json

from pywebpush import webpush, WebPushException
from sqlalchemy.orm import Session

from app.config.push_config import VAPID_PRIVATE_KEY, VAPID_CLAIMS
from app.models.push_subscription import PushSubscription
from app.repositories.push_subscription_repository import PushSubscriptionRepository


class PushService:

    @staticmethod
    def send_to_subscriptions(
        db: Session,
        subscriptions: list[PushSubscription],
        title: str,
        body: str,
        data: dict | None = None,
    ) -> None:

        payload = json.dumps({
            "title": title,
            "body": body,
            "data": data or {},
        })

        for subscription in subscriptions:
            try:
                webpush(
                    subscription_info={
                        "endpoint": subscription.endpoint,
                        "keys": {
                            "p256dh": subscription.p256dh,
                            "auth": subscription.auth,
                        },
                    },
                    data=payload,
                    vapid_private_key=VAPID_PRIVATE_KEY,
                    vapid_claims=dict(VAPID_CLAIMS),
                )
            except WebPushException as error:
                status_code = getattr(error.response, "status_code", None)

                if status_code in (404, 410):
                    # El navegador eliminó la suscripción del lado del cliente.
                    PushSubscriptionRepository.delete_by_endpoint(
                        db, subscription.endpoint
                    )
                else:
                    print(f"⚠️ Error enviando push a {subscription.endpoint}: {error}")