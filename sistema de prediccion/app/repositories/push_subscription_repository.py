from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.push_subscription import PushSubscription


class PushSubscriptionRepository:

    @staticmethod
    def upsert(
        db: Session,
        user_id: int,
        endpoint: str,
        p256dh: str,
        auth: str,
        user_agent: str | None
    ) -> PushSubscription:

        existing = db.scalar(
            select(PushSubscription).where(
                PushSubscription.user_id == user_id,
                PushSubscription.endpoint == endpoint,
            )
        )

        if existing:
            existing.p256dh = p256dh
            existing.auth = auth
            existing.user_agent = user_agent
            db.commit()
            db.refresh(existing)
            return existing

        subscription = PushSubscription(
            user_id=user_id,
            endpoint=endpoint,
            p256dh=p256dh,
            auth=auth,
            user_agent=user_agent,
        )
        db.add(subscription)
        db.commit()
        db.refresh(subscription)
        return subscription

    @staticmethod
    def delete(db: Session, user_id: int, endpoint: str) -> None:
        db.query(PushSubscription).filter(
            PushSubscription.user_id == user_id,
            PushSubscription.endpoint == endpoint,
        ).delete()
        db.commit()

    @staticmethod
    def delete_by_endpoint(db: Session, endpoint: str) -> None:
        db.query(PushSubscription).filter(
            PushSubscription.endpoint == endpoint
        ).delete()
        db.commit()

    @staticmethod
    def get_for_users(db: Session, user_ids: list[int]) -> list[PushSubscription]:
        if not user_ids:
            return []
        return list(
            db.scalars(
                select(PushSubscription).where(
                    PushSubscription.user_id.in_(user_ids)
                )
            ).all()
        )