from datetime import (
    datetime,
    timezone,
)

from sqlalchemy import (
    or_,
    select,
)

from sqlalchemy.orm import Session

from app.models.notification import (
    Notification,
)


class NotificationRepository:

    @staticmethod
    def create(
        db: Session,
        category: str,
        notification_type: str,
        title: str,
        message: str,
        priority: str = "info",
        requires_action: bool = False,
        suggested_action: str | None = None,
        user_id: int | None = None,
        recipient_role: str | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
        payload: dict | None = None
    ) -> Notification:

        notification = Notification(
            user_id=user_id,
            recipient_role=recipient_role,
            category=category,
            notification_type=(
                notification_type
            ),
            title=title,
            message=message,
            priority=priority,
            requires_action=(
                requires_action
            ),
            suggested_action=(
                suggested_action
            ),
            entity_type=entity_type,
            entity_id=entity_id,
            payload=payload
        )

        db.add(notification)
        db.commit()
        db.refresh(notification)

        return notification

    @staticmethod
    def get_by_id(
        db: Session,
        notification_id: int
    ) -> Notification | None:

        return db.get(
            Notification,
            notification_id
        )

    @staticmethod
    def get_for_user(
        db: Session,
        user_id: int,
        roles: list[str] | None = None,
        unread_only: bool = False,
        limit: int = 100
    ) -> list[Notification]:

        conditions = [
            Notification.user_id
            == user_id
        ]

        if roles:

            conditions.append(
                Notification.recipient_role.in_(
                    roles
                )
            )

        statement = (
            select(Notification)
            .where(
                or_(
                    *conditions
                )
            )
            .order_by(
                Notification.created_at.desc()
            )
        )

        if unread_only:

            statement = statement.where(
                Notification.is_read.is_(
                    False
                )
            )

        statement = statement.limit(
            limit
        )

        return list(
            db.scalars(
                statement
            ).all()
        )

    @staticmethod
    def mark_read(
        db: Session,
        notification: Notification
    ) -> Notification:

        notification.is_read = True

        notification.read_at = (
            datetime.now(
                timezone.utc
            )
        )

        db.commit()
        db.refresh(notification)

        return notification

    @staticmethod
    def mark_unread(
        db: Session,
        notification: Notification
    ) -> Notification:

        notification.is_read = False
        notification.read_at = None

        db.commit()
        db.refresh(notification)

        return notification

    @staticmethod
    def acknowledge(
        db: Session,
        notification: Notification
    ) -> Notification:

        notification.acknowledged = True

        notification.acknowledged_at = (
            datetime.now(
                timezone.utc
            )
        )

        if not notification.is_read:

            notification.is_read = True

            notification.read_at = (
                datetime.now(
                    timezone.utc
                )
            )

        db.commit()
        db.refresh(notification)

        return notification