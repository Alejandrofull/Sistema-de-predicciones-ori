from sqlalchemy import delete, select
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

    # ==========================================
    # NUEVOS MÉTODOS — gestión de roles
    # ==========================================

    @staticmethod
    def create(
        db: Session,
        name: str,
        code: str,
        description: str | None
    ) -> Role:

        role = Role(
            name=name,
            code=code,
            description=description,
            is_active=True
        )

        db.add(role)
        db.commit()
        db.refresh(role)

        return role

    @staticmethod
    def set_active(
        db: Session,
        role: Role,
        is_active: bool
    ) -> None:

        role.is_active = is_active
        db.commit()
        db.refresh(role)

    @staticmethod
    def replace_permissions(
        db: Session,
        role_id: int,
        permission_ids: list[int]
    ) -> None:

        db.execute(
            delete(RolePermission).where(
                RolePermission.role_id == role_id
            )
        )

        for permission_id in permission_ids:
            db.add(
                RolePermission(
                    role_id=role_id,
                    permission_id=permission_id
                )
            )

        db.commit()