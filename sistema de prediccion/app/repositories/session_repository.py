from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user_session import UserSession


class SessionRepository:

    @staticmethod
    def create(
        db: Session,
        user_id: int,
        session_uuid: str,
        ip_address: str | None,
        user_agent: str | None,
        device_name: str | None
    ) -> UserSession:
        user_session = UserSession(
            user_id=user_id,
            session_uuid=session_uuid,
            ip_address=ip_address,
            user_agent=user_agent,
            device_name=device_name,
            is_active=True,
            last_activity_at=datetime.now(timezone.utc)
        )

        db.add(user_session)
        db.commit()
        db.refresh(user_session)

        return user_session

    @staticmethod
    def get_by_id(
        db: Session,
        session_id: int
    ) -> UserSession | None:
        return db.get(UserSession, session_id)

    @staticmethod
    def get_by_uuid(
        db: Session,
        session_uuid: str
    ) -> UserSession | None:
        statement = select(UserSession).where(
            UserSession.session_uuid == session_uuid
        )

        return db.scalar(statement)

    @staticmethod
    def get_active_by_user(
        db: Session,
        user_id: int
    ) -> list[UserSession]:
        statement = (
            select(UserSession)
            .where(
                UserSession.user_id == user_id,
                UserSession.is_active.is_(True)
            )
            .order_by(UserSession.created_at.desc())
        )

        return list(db.scalars(statement).all())

    @staticmethod
    def revoke(
        db: Session,
        session: UserSession,
        reason: str
    ) -> None:
        session.is_active = False
        session.revoked_at = datetime.now(timezone.utc)
        session.revoked_reason = reason
        db.commit()

    @staticmethod
    def update_activity(
        db: Session,
        session: UserSession
    ) -> None:
        session.last_activity_at = datetime.now(timezone.utc)
        db.commit()