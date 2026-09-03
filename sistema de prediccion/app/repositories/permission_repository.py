from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.permission import Permission


class PermissionRepository:

    @staticmethod
    def get_by_code(
        db: Session,
        code: str
    ) -> Permission | None:

        statement = select(Permission).where(
            Permission.code == code
        )

        return db.scalar(statement)

    @staticmethod
    def get_all(
        db: Session
    ) -> list[Permission]:

        statement = (
            select(Permission)
            .where(
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