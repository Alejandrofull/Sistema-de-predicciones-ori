from datetime import datetime

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)

from sqlalchemy.orm import Session

from app.database.session import (
    get_db,
)

from app.repositories.audit_log_repository import (
    AuditLogRepository,
)

from app.schemas.audit import (
    AuditLogDetailResponse,
    AuditSummaryResponse,
)

from app.security.permissions import (
    Permissions,
    require_permission,
)

from app.services.audit_service import (
    AuditService,
)


router = APIRouter(
    prefix="/audit",
    tags=["audit"]
)


# ==========================================
# LISTAR LOGS
# ==========================================

@router.get(
    "",
    response_model=(
        AuditSummaryResponse
    )
)
def get_audit_logs(
    user_id: int | None = Query(
        default=None,
        gt=0
    ),

    action: str | None = Query(
        default=None,
        max_length=100
    ),

    entity: str | None = Query(
        default=None,
        max_length=100
    ),

    entity_id: str | None = Query(
        default=None,
        max_length=100
    ),

    start_date: datetime | None = Query(
        default=None
    ),

    end_date: datetime | None = Query(
        default=None
    ),

    limit: int = Query(
        default=100,
        ge=1,
        le=1000
    ),

    offset: int = Query(
        default=0,
        ge=0
    ),

    current_user=Depends(
        require_permission(
            Permissions.AUDIT_VIEW
        )
    ),

    db: Session = Depends(
        get_db
    )
):

    logs = (
        AuditLogRepository.get_all(
            db=db,
            user_id=user_id,
            action=(
                action.strip().lower()
                if action
                else None
            ),
            entity=(
                entity.strip().lower()
                if entity
                else None
            ),
            entity_id=(
                entity_id
            ),
            start_date=(
                start_date
            ),
            end_date=(
                end_date
            ),
            limit=limit,
            offset=offset
        )
    )

    serialized_logs = [
        AuditLogDetailResponse(
            id=log.id,
            user_id=(
                log.user_id
            ),
            action=(
                log.action
            ),
            entity=(
                log.entity
            ),
            entity_id=(
                log.entity_id
            ),
            details=(
                AuditService.parse_details(
                    log.details
                )
            ),
            created_at=(
                log.created_at
            )
        )
        for log
        in logs
    ]

    return {
        "total_returned": (
            len(
                serialized_logs
            )
        ),
        "logs": (
            serialized_logs
        )
    }


# ==========================================
# OBTENER LOG
# ==========================================

@router.get(
    "/{audit_log_id}",
    response_model=(
        AuditLogDetailResponse
    )
)
def get_audit_log(
    audit_log_id: int,

    current_user=Depends(
        require_permission(
            Permissions.AUDIT_VIEW
        )
    ),

    db: Session = Depends(
        get_db
    )
):

    log = (
        AuditLogRepository.get_by_id(
            db,
            audit_log_id
        )
    )

    if not log:

        raise HTTPException(
            status_code=404,
            detail=(
                "Registro de auditoría "
                "no encontrado"
            )
        )

    return (
        AuditLogDetailResponse(
            id=log.id,
            user_id=(
                log.user_id
            ),
            action=(
                log.action
            ),
            entity=(
                log.entity
            ),
            entity_id=(
                log.entity_id
            ),
            details=(
                AuditService.parse_details(
                    log.details
                )
            ),
            created_at=(
                log.created_at
            )
        )
    )