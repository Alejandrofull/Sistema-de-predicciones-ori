from __future__ import annotations

import json

from datetime import (
    date,
    datetime,
)

from decimal import Decimal
from enum import Enum
from typing import Any

from sqlalchemy.orm import Session

from app.repositories.audit_log_repository import (
    AuditLogRepository,
)


class AuditService:

    # ==========================================
    # REGISTRO NORMAL
    # ==========================================

    @staticmethod
    def log(
        db: Session,
        action: str,
        user_id: int | None = None,
        entity: str | None = None,
        entity_id: (
            int
            | str
            | None
        ) = None,
        details: (
            dict
            | list
            | str
            | None
        ) = None
    ):

        normalized_action = (
            AuditService
            ._normalize_required_text(
                action
            )
        )

        normalized_entity = (
            AuditService
            ._normalize_optional_text(
                entity
            )
        )

        normalized_entity_id = (
            str(
                entity_id
            )
            if entity_id is not None
            else None
        )

        serialized_details = (
            AuditService
            ._serialize_details(
                details
            )
        )

        return (
            AuditLogRepository.create(
                db=db,
                user_id=user_id,
                action=(
                    normalized_action
                ),
                entity=(
                    normalized_entity
                ),
                entity_id=(
                    normalized_entity_id
                ),
                details=(
                    serialized_details
                )
            )
        )

    # ==========================================
    # REGISTRO SEGURO
    # ==========================================

    @staticmethod
    def log_safe(
        db: Session,
        action: str,
        user_id: int | None = None,
        entity: str | None = None,
        entity_id: (
            int
            | str
            | None
        ) = None,
        details: (
            dict
            | list
            | str
            | None
        ) = None
    ) -> bool:

        try:

            AuditService.log(
                db=db,
                action=action,
                user_id=user_id,
                entity=entity,
                entity_id=entity_id,
                details=details
            )

            return True

        except Exception as error:

            try:
                db.rollback()

            except Exception:
                pass

            print(
                "⚠️ No se pudo registrar "
                "auditoría:"
            )

            print(
                f"   action={action}"
            )

            print(
                f"   error={error}"
            )

            return False

    # ==========================================
    # SERIALIZAR DETALLES
    # ==========================================

    @staticmethod
    def _serialize_details(
        details
    ) -> str | None:

        if details is None:
            return None

        if isinstance(
            details,
            str
        ):
            return details

        return json.dumps(
            details,
            ensure_ascii=False,
            default=(
                AuditService
                ._json_default
            ),
            separators=(
                ",",
                ":"
            )
        )

    # ==========================================
    # PARSEAR DETALLES
    # ==========================================

    @staticmethod
    def parse_details(
        details: str | None
    ):

        if details is None:
            return None

        try:

            return json.loads(
                details
            )

        except (
            json.JSONDecodeError,
            TypeError,
        ):

            return details

    # ==========================================
    # JSON AUXILIAR
    # ==========================================

    @staticmethod
    def _json_default(
        value: Any
    ):

        if isinstance(
            value,
            (
                datetime,
                date,
            )
        ):
            return value.isoformat()

        if isinstance(
            value,
            Decimal
        ):
            return float(
                value
            )

        if isinstance(
            value,
            Enum
        ):
            return value.value

        return str(
            value
        )

    # ==========================================
    # NORMALIZACIONES
    # ==========================================

    @staticmethod
    def _normalize_required_text(
        value: str
    ) -> str:

        normalized = (
            str(
                value
            )
            .strip()
            .lower()
        )

        if not normalized:

            raise ValueError(
                "action es obligatorio"
            )

        return normalized[
            :100
        ]

    @staticmethod
    def _normalize_optional_text(
        value: str | None
    ) -> str | None:

        if value is None:
            return None

        normalized = (
            str(
                value
            )
            .strip()
            .lower()
        )

        if not normalized:
            return None

        return normalized[
            :100
        ]