from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.export import Export


class ExportRepository:

    @staticmethod
    def create(
        db: Session,
        user_id: int,
        filename: str,
        export_format: str,
        storage_path: str,
        status: str = "completed"
    ) -> Export:

        export = Export(
            user_id=user_id,
            filename=filename,
            export_format=export_format,
            storage_path=storage_path,
            status=status
        )

        db.add(export)
        db.commit()
        db.refresh(export)

        return export

    @staticmethod
    def get_by_id(
        db: Session,
        export_id: int
    ) -> Export | None:

        return db.get(
            Export,
            export_id
        )

    @staticmethod
    def get_by_user(
        db: Session,
        user_id: int
    ) -> list[Export]:

        statement = (
            select(Export)
            .where(
                Export.user_id == user_id
            )
            .order_by(
                Export.created_at.desc()
            )
        )

        return list(
            db.scalars(statement).all()
        )

    @staticmethod
    def get_all(
        db: Session
    ) -> list[Export]:

        statement = (
            select(Export)
            .order_by(
                Export.created_at.desc()
            )
        )

        return list(
            db.scalars(statement).all()
        )

    @staticmethod
    def delete(
        db: Session,
        export: Export
    ) -> None:

        db.delete(export)
        db.commit()