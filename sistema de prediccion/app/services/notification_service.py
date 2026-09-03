from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories.notification_repository import (
    NotificationRepository,
)

from app.services.audit_service import (
    AuditService,
)

from app.services.authorization_service import (
    AuthorizationService,
)


class NotificationService:

    # ==========================================
    # OBTENER NOTIFICACIONES
    # ==========================================

    @staticmethod
    def get_user_notifications(
        db: Session,
        user_id: int,
        unread_only: bool,
        limit: int
    ):

        roles = (
            AuthorizationService
            .get_user_roles(
                db=db,
                user_id=user_id
            )
        )

        return (
            NotificationRepository
            .get_for_user(
                db=db,
                user_id=user_id,
                roles=roles,
                unread_only=(
                    unread_only
                ),
                limit=limit
            )
        )

    # ==========================================
    # MARCAR LEÍDA
    # ==========================================

    @staticmethod
    def mark_read(
        db: Session,
        notification_id: int,
        user_id: int
    ):

        notification = (
            NotificationRepository
            .get_by_id(
                db,
                notification_id
            )
        )

        if not notification:

            raise HTTPException(
                status_code=404,
                detail=(
                    "Notificación no encontrada"
                )
            )

        NotificationService._validate_access(
            notification=notification,
            user_id=user_id,
            db=db
        )

        notification = (
            NotificationRepository
            .mark_read(
                db=db,
                notification=notification
            )
        )

        return notification

    # ==========================================
    # RECONOCER NOTIFICACIÓN
    # ==========================================

    @staticmethod
    def acknowledge(
        db: Session,
        notification_id: int,
        user_id: int
    ):

        notification = (
            NotificationRepository
            .get_by_id(
                db,
                notification_id
            )
        )

        if not notification:

            raise HTTPException(
                status_code=404,
                detail=(
                    "Notificación no encontrada"
                )
            )

        NotificationService._validate_access(
            notification=notification,
            user_id=user_id,
            db=db
        )

        notification = (
            NotificationRepository
            .acknowledge(
                db=db,
                notification=notification
            )
        )

        AuditService.log_safe(
            db=db,
            user_id=user_id,
            action=(
                "notification.acknowledge"
            ),
            entity="notification",
            entity_id=(
                notification.id
            ),
            details={
                "category": (
                    notification.category
                ),
                "notification_type": (
                    notification
                    .notification_type
                ),
                "priority": (
                    notification.priority
                ),
                "entity_type": (
                    notification.entity_type
                ),
                "entity_id": (
                    notification.entity_id
                ),
            }
        )

        return notification

    # ==========================================
    # VALIDAR ACCESO
    # ==========================================

    @staticmethod
    def _validate_access(
        notification,
        user_id: int,
        db: Session
    ) -> None:

        # ==========================================
        # NOTIFICACIÓN DIRECTA AL USUARIO
        # ==========================================

        if (
            notification.user_id
            is not None
            and notification.user_id
            == user_id
        ):

            return

        # ==========================================
        # NOTIFICACIÓN POR ROL
        # ==========================================

        if (
            notification.recipient_role
            is not None
        ):

            roles = (
                AuthorizationService
                .get_user_roles(
                    db=db,
                    user_id=user_id
                )
            )

            if (
                notification.recipient_role
                in roles
            ):

                return

        # ==========================================
        # NOTIFICACIÓN SIN DESTINO ESPECÍFICO
        # ==========================================

        if (
            notification.user_id
            is None
            and notification.recipient_role
            is None
        ):

            return

        raise HTTPException(
            status_code=403,
            detail=(
                "No tiene acceso "
                "a esta notificación"
            )
        )