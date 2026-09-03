from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    select,
)

from sqlalchemy.orm import Session

from app.models.audit_log import (
    AuditLog,
)


class AuditLogRepository:

    @staticmethod
    def create(
        db: Session,
        action: str,
        user_id: int | None = None,
        entity: str | None = None,
        entity_id: str | None = None,
        details: str | None = None
    ) -> AuditLog:

        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            entity=entity,
            entity_id=entity_id,
            details=details
        )

        db.add(
            audit_log
        )

        db.commit()

        db.refresh(
            audit_log
        )

        return audit_log

    @staticmethod
    def get_by_id(
        db: Session,
        audit_log_id: int
    ) -> AuditLog | None:

        return db.get(
            AuditLog,
            audit_log_id
        )

    @staticmethod
    def get_all(
        db: Session,
        user_id: int | None = None,
        action: str | None = None,
        entity: str | None = None,
        entity_id: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 100,
        offset: int = 0
    ) -> list[AuditLog]:

        statement = (
            select(
                AuditLog
            )
            .order_by(
                AuditLog.created_at.desc(),
                AuditLog.id.desc()
            )
        )

        if user_id is not None:

            statement = statement.where(
                AuditLog.user_id
                == user_id
            )

        if action:

            statement = statement.where(
                AuditLog.action
                == action
            )

        if entity:

            statement = statement.where(
                AuditLog.entity
                == entity
            )

        if entity_id:

            statement = statement.where(
                AuditLog.entity_id
                == entity_id
            )

        if start_date is not None:

            statement = statement.where(
                AuditLog.created_at
                >= start_date
            )

        if end_date is not None:

            statement = statement.where(
                AuditLog.created_at
                <= end_date
            )

        statement = (
            statement
            .offset(
                offset
            )
            .limit(
                limit
            )
        )

        return list(
            db.scalars(
                statement
            ).all()
        )

    @staticmethod
    def get_by_user(
        db: Session,
        user_id: int,
        limit: int = 100
    ) -> list[AuditLog]:

        statement = (
            select(
                AuditLog
            )
            .where(
                AuditLog.user_id
                == user_id
            )
            .order_by(
                AuditLog.created_at.desc()
            )
            .limit(
                limit
            )
        )

        return list(
            db.scalars(
                statement
            ).all()
        )

    @staticmethod
    def get_by_entity(
        db: Session,
        entity: str,
        entity_id: str,
        limit: int = 100
    ) -> list[AuditLog]:

        statement = (
            select(
                AuditLog
            )
            .where(
                AuditLog.entity
                == entity,
                AuditLog.entity_id
                == entity_id
            )
            .order_by(
                AuditLog.created_at.desc()
            )
            .limit(
                limit
            )
        )

        return list(
            db.scalars(
                statement
            ).all()
        )