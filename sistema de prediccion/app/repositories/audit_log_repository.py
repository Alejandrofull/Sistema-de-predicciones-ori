from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.user import User


class AuditLogRepository:

    # ==========================================
    # HELPER: aplica los mismos filtros a cualquier statement
    # ==========================================
    @staticmethod
    def _apply_filters(
        statement,
        user_id: int | None = None,
        action: str | None = None,
        entity: str | None = None,
        entity_id: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ):
        if user_id is not None:
            statement = statement.where(AuditLog.user_id == user_id)

        if action:
            statement = statement.where(AuditLog.action == action)

        if entity:
            statement = statement.where(AuditLog.entity == entity)

        if entity_id:
            statement = statement.where(AuditLog.entity_id == entity_id)

        if start_date is not None:
            statement = statement.where(AuditLog.created_at >= start_date)

        if end_date is not None:
            statement = statement.where(AuditLog.created_at <= end_date)

        return statement

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

        db.add(audit_log)
        db.commit()
        db.refresh(audit_log)

        return audit_log

    @staticmethod
    def get_by_id(
        db: Session,
        audit_log_id: int
    ) -> AuditLog | None:

        return db.get(AuditLog, audit_log_id)

    # ==========================================
    # LISTAR CON EMAIL DEL USUARIO (JOIN)
    # ==========================================
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
    ) -> list[tuple[AuditLog, str | None]]:
        """
        Devuelve tuplas (AuditLog, user_email).
        user_email es None si el log no tiene user_id
        o si el usuario fue eliminado.
        """

        statement = (
            select(AuditLog, User.email)
            .outerjoin(User, User.id == AuditLog.user_id)
            .order_by(
                AuditLog.created_at.desc(),
                AuditLog.id.desc()
            )
        )

        statement = AuditLogRepository._apply_filters(
            statement,
            user_id=user_id,
            action=action,
            entity=entity,
            entity_id=entity_id,
            start_date=start_date,
            end_date=end_date,
        )

        statement = statement.offset(offset).limit(limit)

        rows = db.execute(statement).all()

        return [(row[0], row[1]) for row in rows]

    # ==========================================
    # CONTEO TOTAL (para paginación real)
    # ==========================================
    @staticmethod
    def count_all(
        db: Session,
        user_id: int | None = None,
        action: str | None = None,
        entity: str | None = None,
        entity_id: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> int:

        statement = select(func.count(AuditLog.id))

        statement = AuditLogRepository._apply_filters(
            statement,
            user_id=user_id,
            action=action,
            entity=entity,
            entity_id=entity_id,
            start_date=start_date,
            end_date=end_date,
        )

        return db.scalar(statement) or 0

    # ==========================================
    # VALORES DISTINTOS (para selects del frontend)
    # ==========================================
    @staticmethod
    def get_distinct_actions(db: Session) -> list[str]:
        statement = (
            select(AuditLog.action)
            .distinct()
            .order_by(AuditLog.action)
        )
        return list(db.scalars(statement).all())

    @staticmethod
    def get_distinct_entities(db: Session) -> list[str]:
        statement = (
            select(AuditLog.entity)
            .where(AuditLog.entity.is_not(None))
            .distinct()
            .order_by(AuditLog.entity)
        )
        return list(db.scalars(statement).all())

    @staticmethod
    def get_by_user(
        db: Session,
        user_id: int,
        limit: int = 100
    ) -> list[AuditLog]:

        statement = (
            select(AuditLog)
            .where(AuditLog.user_id == user_id)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
        )

        return list(db.scalars(statement).all())

    @staticmethod
    def get_by_entity(
        db: Session,
        entity: str,
        entity_id: str,
        limit: int = 100
    ) -> list[AuditLog]:

        statement = (
            select(AuditLog)
            .where(
                AuditLog.entity == entity,
                AuditLog.entity_id == entity_id
            )
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
        )

        return list(db.scalars(statement).all())