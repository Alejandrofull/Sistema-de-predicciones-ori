from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.training import Training


class TrainingRepository:

    @staticmethod
    def create(
        db: Session,
        dataset_id: int,
        model_id: int | None = None,
        status: str = "pending",
        started_at: datetime | None = None,
        finished_at: datetime | None = None
    ) -> Training:

        training = Training(
            dataset_id=dataset_id,
            model_id=model_id,
            status=status,
            started_at=started_at,
            finished_at=finished_at
        )

        db.add(training)
        db.commit()
        db.refresh(training)

        return training

    @staticmethod
    def get_by_id(
        db: Session,
        training_id: int
    ) -> Training | None:

        return db.get(
            Training,
            training_id
        )

    @staticmethod
    def get_all(
        db: Session
    ) -> list[Training]:

        statement = (
            select(Training)
            .order_by(
                Training.created_at.desc()
            )
        )

        return list(
            db.scalars(statement).all()
        )

    @staticmethod
    def get_by_dataset(
        db: Session,
        dataset_id: int
    ) -> list[Training]:

        statement = (
            select(Training)
            .where(
                Training.dataset_id == dataset_id
            )
            .order_by(
                Training.created_at.desc()
            )
        )

        return list(
            db.scalars(statement).all()
        )

    @staticmethod
    def mark_running(
        db: Session,
        training: Training
    ) -> Training:

        training.status = "running"

        training.started_at = (
            datetime.now(
                timezone.utc
            )
        )

        db.commit()
        db.refresh(training)

        return training

    @staticmethod
    def mark_completed(
        db: Session,
        training: Training,
        model_id: int
    ) -> Training:

        training.model_id = model_id
        training.status = "completed"

        training.finished_at = (
            datetime.now(
                timezone.utc
            )
        )

        db.commit()
        db.refresh(training)

        return training

    @staticmethod
    def mark_failed(
        db: Session,
        training: Training
    ) -> Training:

        training.status = "failed"

        training.finished_at = (
            datetime.now(
                timezone.utc
            )
        )

        db.commit()
        db.refresh(training)

        return training