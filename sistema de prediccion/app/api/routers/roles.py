from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.repositories.permission_repository import (
    PermissionRepository
)
from app.repositories.role_repository import (
    RoleRepository
)
from app.schemas.role import (
    PermissionResponse,
    RoleCreateRequest,
    RoleDetailResponse,
    RolePermissionsUpdate,
    RoleResponse,
    RoleStatusUpdate,
)
from app.security.permissions import (
    Permissions,
    require_permission
)
from app.services.audit_service import AuditService


router = APIRouter(
    prefix="/roles",
    tags=["roles"]
)


# ==========================================
# LISTAR ROLES
# ==========================================

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


# ==========================================
# LISTAR TODOS LOS PERMISOS DEL SISTEMA
# ==========================================

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


# ==========================================
# VER PERMISOS DE UN ROL (solo lectura)
# ==========================================

@router.get(
    "/{role_id}/permissions",
    response_model=RoleDetailResponse
)
def get_role_permissions(
    role_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_permission(
            Permissions.USERS_MANAGE
        )
    )
):
    role = RoleRepository.get_by_id(db, role_id)

    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rol no encontrado"
        )

    permissions = RoleRepository.get_permissions(db, role_id)

    return {
        "id": role.id,
        "name": role.name,
        "code": role.code,
        "description": role.description,
        "is_active": role.is_active,
        "permissions": permissions,
    }


# ==========================================
# CREAR ROL
# ==========================================

@router.post(
    "",
    response_model=RoleResponse
)
def create_role(
    body: RoleCreateRequest,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_permission(
            Permissions.USERS_MANAGE
        )
    )
):
    existing = RoleRepository.get_by_code(db, body.code)

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un rol con ese código"
        )

    role = RoleRepository.create(
        db=db,
        name=body.name,
        code=body.code,
        description=body.description
    )

    AuditService.log_safe(
        db=db,
        user_id=current_user.id,
        action="role.create",
        entity="role",
        entity_id=role.id,
        details={
            "name": body.name,
            "code": body.code,
        },
    )

    return role


# ==========================================
# REEMPLAZAR PERMISOS DE UN ROL
# ==========================================

@router.put(
    "/{role_id}/permissions",
    response_model=RoleDetailResponse
)
def update_role_permissions(
    role_id: int,
    body: RolePermissionsUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_permission(
            Permissions.USERS_MANAGE
        )
    )
):
    role = RoleRepository.get_by_id(db, role_id)

    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rol no encontrado"
        )

    RoleRepository.replace_permissions(
        db=db,
        role_id=role_id,
        permission_ids=body.permission_ids
    )

    AuditService.log_safe(
        db=db,
        user_id=current_user.id,
        action="role.permissions.update",
        entity="role",
        entity_id=role_id,
        details={
            "permission_ids": body.permission_ids,
        },
    )

    permissions = RoleRepository.get_permissions(db, role_id)

    return {
        "id": role.id,
        "name": role.name,
        "code": role.code,
        "description": role.description,
        "is_active": role.is_active,
        "permissions": permissions,
    }


# ==========================================
# ACTIVAR / DESACTIVAR ROL
# ==========================================

@router.patch(
    "/{role_id}/status",
    response_model=RoleResponse
)
def update_role_status(
    role_id: int,
    body: RoleStatusUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_permission(
            Permissions.USERS_MANAGE
        )
    )
):
    role = RoleRepository.get_by_id(db, role_id)

    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rol no encontrado"
        )

    RoleRepository.set_active(
        db=db,
        role=role,
        is_active=body.is_active
    )

    AuditService.log_safe(
        db=db,
        user_id=current_user.id,
        action="role.status.update",
        entity="role",
        entity_id=role_id,
        details={
            "is_active": body.is_active,
        },
    )

    return role