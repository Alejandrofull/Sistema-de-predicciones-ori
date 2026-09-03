from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.permission import Permission
from app.repositories.permission_repository import (
    PermissionRepository
)
from app.repositories.role_repository import (
    RoleRepository
)
from app.schemas.role import (
    PermissionResponse,
    RoleResponse
)
from app.security.permissions import (
    Permissions,
    require_permission
)


router = APIRouter(
    prefix="/roles",
    tags=["roles"]
)


@router.get(
    "",
    response_model=list[RoleResponse]
)
def get_roles(
    db: Session = Depends(get_db),
    current_user=Depends(
        require_permission(
            Permissions.USERS_MANAGE
        )
    )
):
    return RoleRepository.get_active(db)


@router.get(
    "/permissions",
    response_model=list[PermissionResponse]
)
def get_permissions(
    db: Session = Depends(get_db),
    current_user=Depends(
        require_permission(
            Permissions.USERS_MANAGE
        )
    )
):
    return PermissionRepository.get_all(db)