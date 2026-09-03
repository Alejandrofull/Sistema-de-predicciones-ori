from datetime import (
    datetime,
    timezone,
)

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.retraining_runs import (
    RetrainingRun,
)


class RetrainingRunRepository:

    @staticmethod
    def create(
        db: Session,
        model_id: int,
        dataset_id: int,
        trigger_type: str,
        previous_version_id: int | None = None,
        new_version_id: int | None = None,
        reason: str | None = None,
        status: str = "pending"
    ) -> RetrainingRun:

        run = RetrainingRun(
            model_id=model_id,
            previous_version_id=(
                previous_version_id
            ),
            new_version_id=(
                new_version_id
            ),
            dataset_id=dataset_id,
            trigger_type=trigger_type,
            reason=reason,
            status=status
        )

        db.add(run)
        db.commit()
        db.refresh(run)

        return run

    @staticmethod
    def get_by_id(
        db: Session,
        run_id: int
    ) -> RetrainingRun | None:

        return db.get(
            RetrainingRun,
            run_id
        )

    @staticmethod
    def get_all(
        db: Session
    ) -> list[RetrainingRun]:

        statement = (
            select(RetrainingRun)
            .order_by(
                RetrainingRun.created_at.desc()
            )
        )

        return list(
            db.scalars(
                statement
            ).all()
        )

    @staticmethod
    def get_by_model(
        db: Session,
        model_id: int
    ) -> list[RetrainingRun]:

        statement = (
            select(RetrainingRun)
            .where(
                RetrainingRun.model_id
                == model_id
            )
            .order_by(
                RetrainingRun.created_at.desc()
            )
        )

        return list(
            db.scalars(
                statement
            ).all()
        )

    @staticmethod
    def get_running_by_model(
        db: Session,
        model_id: int
    ) -> RetrainingRun | None:

        statement = (
            select(RetrainingRun)
            .where(
                RetrainingRun.model_id
                == model_id,
                RetrainingRun.status.in_(
                    [
                        "pending",
                        "running",
                    ]
                )
            )
            .order_by(
                RetrainingRun.created_at.desc()
            )
            .limit(1)
        )

        return db.scalar(
            statement
        )

    @staticmethod
    def mark_running(
        db: Session,
        run: RetrainingRun
    ) -> RetrainingRun:

        run.status = "running"

        run.started_at = (
            datetime.now(
                timezone.utc
            )
        )

        db.commit()
        db.refresh(run)

        return run

    @staticmethod
    def mark_completed(
        db: Session,
        run: RetrainingRun,
        new_version_id: int
    ) -> RetrainingRun:

        run.new_version_id = (
            new_version_id
        )

        run.status = "completed"

        run.finished_at = (
            datetime.now(
                timezone.utc
            )
        )

        db.commit()
        db.refresh(run)

        return run

    @staticmethod
    def mark_failed(
        db: Session,
        run: RetrainingRun,
        reason: str | None = None
    ) -> RetrainingRun:

        run.status = "failed"

        if reason:
            run.reason = reason

        run.finished_at = (
            datetime.now(
                timezone.utc
            )
        )

        db.commit()
        db.refresh(run)

        return run