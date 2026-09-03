from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.role import Role
from app.models.user_role import UserRole


class UserRoleRepository:

    @staticmethod
    def assign_role(
        db: Session,
        user_id: int,
        role_id: int
    ) -> UserRole:

        existing = db.scalar(
            select(UserRole).where(
                UserRole.user_id == user_id,
                UserRole.role_id == role_id
            )
        )

        if existing:
            return existing

        user_role = UserRole(
            user_id=user_id,
            role_id=role_id
        )

        db.add(user_role)
        db.commit()
        db.refresh(user_role)

        return user_role

    @staticmethod
    def get_roles_by_user(
        db: Session,
        user_id: int
    ) -> list[Role]:

        statement = (
            select(Role)
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
    def replace_roles(
        db: Session,
        user_id: int,
        role_ids: list[int]
    ) -> None:

        db.execute(
            delete(UserRole).where(
                UserRole.user_id == user_id
            )
        )

        for role_id in role_ids:
            db.add(
                UserRole(
                    user_id=user_id,
                    role_id=role_id
                )
            )

        db.commit()

    @staticmethod
    def remove_role(
        db: Session,
        user_id: int,
        role_id: int
    ) -> None:

        db.execute(
            delete(UserRole).where(
                UserRole.user_id == user_id,
                UserRole.role_id == role_id
            )
        )

        db.commit()