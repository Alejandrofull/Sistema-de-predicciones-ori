from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.user_role import UserRole


class AuthorizationService:

    @staticmethod
    def get_user_roles(
        db: Session,
        user_id: int
    ) -> list[str]:
        statement = (
            select(Role.code)
            .join(
                UserRole,
                UserRole.role_id == Role.id
            )
            .where(
                UserRole.user_id == user_id,
                Role.is_active.is_(True)
            )
            .order_by(Role.id)
        )

        return list(
            db.scalars(statement).all()
        )

    @staticmethod
    def get_user_permission_codes(
        db: Session,
        user_id: int
    ) -> set[str]:
        statement = (
            select(Permission.code)
            .join(
                RolePermission,
                RolePermission.permission_id
                == Permission.id
            )
            .join(
                UserRole,
                UserRole.role_id
                == RolePermission.role_id
            )
            .join(
                Role,
                Role.id == UserRole.role_id
            )
            .where(
                UserRole.user_id == user_id,
                Role.is_active.is_(True),
                Permission.is_active.is_(True)
            )
            .distinct()
        )

        return set(
            db.scalars(statement).all()
        )

    @staticmethod
    def has_permission(
        db: Session,
        user_id: int,
        permission_code: str
    ) -> bool:
        permissions = (
            AuthorizationService
            .get_user_permission_codes(
                db,
                user_id
            )
        )

        return permission_code in permissions

    @staticmethod
    def has_any_permission(
        db: Session,
        user_id: int,
        permission_codes: list[str]
    ) -> bool:
        permissions = (
            AuthorizationService
            .get_user_permission_codes(
                db,
                user_id
            )
        )

        return any(
            code in permissions
            for code in permission_codes
        )

    @staticmethod
    def has_all_permissions(
        db: Session,
        user_id: int,
        permission_codes: list[str]
    ) -> bool:
        permissions = (
            AuthorizationService
            .get_user_permission_codes(
                db,
                user_id
            )
        )

        return all(
            code in permissions
            for code in permission_codes
        )