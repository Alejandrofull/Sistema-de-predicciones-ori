from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.report import Report


class ReportRepository:

    @staticmethod
    def create(
        db: Session,
        user_id: int,
        filename: str,
        report_format: str,
        storage_path: str,
        status: str = "completed"
    ) -> Report:

        report = Report(
            user_id=user_id,
            filename=filename,
            report_format=report_format,
            storage_path=storage_path,
            status=status
        )

        db.add(report)
        db.commit()
        db.refresh(report)

        return report

    @staticmethod
    def get_by_id(
        db: Session,
        report_id: int
    ) -> Report | None:

        return db.get(
            Report,
            report_id
        )

    @staticmethod
    def get_by_user(
        db: Session,
        user_id: int
    ) -> list[Report]:

        statement = (
            select(Report)
            .where(
                Report.user_id == user_id
            )
            .order_by(
                Report.created_at.desc()
            )
        )

        return list(
            db.scalars(statement).all()
        )

    @staticmethod
    def get_all(
        db: Session
    ) -> list[Report]:

        statement = (
            select(Report)
            .order_by(
                Report.created_at.desc()
            )
        )

        return list(
            db.scalars(statement).all()
        )

    @staticmethod
    def delete(
        db: Session,
        report: Report
    ) -> None:

        db.delete(report)
        db.commit()