from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission


class RoleRepository:

    @staticmethod
    def get_by_id(
        db: Session,
        role_id: int
    ) -> Role | None:
        return db.get(Role, role_id)

    @staticmethod
    def get_by_code(
        db: Session,
        code: str
    ) -> Role | None:
        statement = select(Role).where(
            Role.code == code
        )

        return db.scalar(statement)

    @staticmethod
    def get_all(
        db: Session
    ) -> list[Role]:
        statement = (
            select(Role)
            .order_by(Role.id)
        )

        return list(
            db.scalars(statement).all()
        )

    @staticmethod
    def get_active(
        db: Session
    ) -> list[Role]:
        statement = (
            select(Role)
            .where(Role.is_active.is_(True))
            .order_by(Role.id)
        )

        return list(
            db.scalars(statement).all()
        )

    @staticmethod
    def get_permissions(
        db: Session,
        role_id: int
    ) -> list[Permission]:
        statement = (
            select(Permission)
            .join(
                RolePermission,
                RolePermission.permission_id
                == Permission.id
            )
            .where(
                RolePermission.role_id == role_id,
                Permission.is_active.is_(True)
            )
            .order_by(
                Permission.module,
                Permission.code
            )
        )

        return list(
            db.scalars(statement).all()
        )