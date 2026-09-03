from fastapi import (
    APIRouter,
    Depends,
)

from sqlalchemy.orm import Session

from app.database.session import (
    get_db,
)

from app.schemas.user_management import (
    UserManagementResponse,
    UserRoleUpdate,
    UserStatusUpdate,
)

from app.security.permissions import (
    Permissions,
    require_permission,
)

from app.services.audit_service import (
    AuditService,
)

from app.services.user_management_service import (
    UserManagementService,
)


router = APIRouter(
    prefix="/users",
    tags=["users"],
)


# ==========================================
# LISTAR USUARIOS
# ==========================================

@router.get(
    "",
    response_model=list[
        UserManagementResponse
    ],
)
def get_users(
    db: Session = Depends(
        get_db
    ),
    current_user=Depends(
        require_permission(
            Permissions.USERS_VIEW
        )
    ),
):

    return (
        UserManagementService
        .get_all_users(
            db
        )
    )


# ==========================================
# OBTENER USUARIO
# ==========================================

@router.get(
    "/{user_id}",
    response_model=(
        UserManagementResponse
    ),
)
def get_user(
    user_id: int,
    db: Session = Depends(
        get_db
    ),
    current_user=Depends(
        require_permission(
            Permissions.USERS_VIEW
        )
    ),
):

    return (
        UserManagementService
        .get_user_with_roles(
            db,
            user_id,
        )
    )


# ==========================================
# CAMBIAR ESTADO DE USUARIO
# ==========================================

@router.patch(
    "/{user_id}/status",
    response_model=(
        UserManagementResponse
    ),
)
def update_user_status(
    user_id: int,
    body: UserStatusUpdate,
    db: Session = Depends(
        get_db
    ),
    current_user=Depends(
        require_permission(
            Permissions.USERS_MANAGE
        )
    ),
):

    result = (
        UserManagementService
        .update_status(
            db=db,
            user_id=user_id,
            is_active=(
                body.is_active
            ),
        )
    )

    AuditService.log_safe(
        db=db,
        user_id=current_user.id,
        action="user.status.update",
        entity="user",
        entity_id=user_id,
        details={
            "is_active": (
                body.is_active
            ),
        },
    )

    return result


# ==========================================
# REEMPLAZAR ROLES
# ==========================================

@router.put(
    "/{user_id}/roles",
    response_model=(
        UserManagementResponse
    ),
)
def update_user_roles(
    user_id: int,
    body: UserRoleUpdate,
    db: Session = Depends(
        get_db
    ),
    current_user=Depends(
        require_permission(
            Permissions.ROLES_ASSIGN
        )
    ),
):

    result = (
        UserManagementService
        .replace_roles(
            db=db,
            user_id=user_id,
            role_codes=(
                body.role_codes
            ),
        )
    )

    AuditService.log_safe(
        db=db,
        user_id=current_user.id,
        action="role.assign",
        entity="user",
        entity_id=user_id,
        details={
            "role_codes": (
                list(
                    body.role_codes
                )
            ),
        },
    )

    return result