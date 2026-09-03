from datetime import (
    date,
    datetime,
    timezone,
)

from sqlalchemy import (
    select,
)

from sqlalchemy.orm import Session

from app.models.prediction import (
    Prediction,
)


class PredictionRepository:

    @staticmethod
    def create(
        db: Session,
        user_id: int | None,
        model_id: int,
        model_version_id: int | None,
        dataset_id: int | None,
        business_series_id: int | None,
        horizon: int,
        start_date: date,
        end_date: date,
        status: str = "running"
    ) -> Prediction:

        prediction = Prediction(
            user_id=user_id,
            model_id=model_id,
            model_version_id=model_version_id,
            dataset_id=dataset_id,
            business_series_id=(
                business_series_id
            ),
            horizon=horizon,
            start_date=start_date,
            end_date=end_date,
            status=status
        )

        db.add(
            prediction
        )

        db.commit()

        db.refresh(
            prediction
        )

        return prediction

    @staticmethod
    def get_by_id(
        db: Session,
        prediction_id: int
    ) -> Prediction | None:

        return db.get(
            Prediction,
            prediction_id
        )

    @staticmethod
    def get_by_user(
        db: Session,
        user_id: int
    ) -> list[Prediction]:

        statement = (
            select(
                Prediction
            )
            .where(
                Prediction.user_id
                == user_id
            )
            .order_by(
                Prediction.created_at.desc()
            )
        )

        return list(
            db.scalars(
                statement
            ).all()
        )

    # ==========================================
    # POR SERIE DE NEGOCIO
    # ==========================================

    @staticmethod
    def get_by_business_series(
        db: Session,
        business_series_id: int,
        limit: int | None = None
    ) -> list[Prediction]:

        statement = (
            select(
                Prediction
            )
            .where(
                Prediction.business_series_id
                == business_series_id
            )
            .order_by(
                Prediction.created_at.desc()
            )
        )

        if limit is not None:

            statement = (
                statement.limit(
                    limit
                )
            )

        return list(
            db.scalars(
                statement
            ).all()
        )

    @staticmethod
    def get_all(
        db: Session
    ) -> list[Prediction]:

        statement = (
            select(
                Prediction
            )
            .order_by(
                Prediction.created_at.desc()
            )
        )

        return list(
            db.scalars(
                statement
            ).all()
        )

    @staticmethod
    def mark_completed(
        db: Session,
        prediction: Prediction
    ) -> Prediction:

        prediction.status = (
            "completed"
        )

        prediction.completed_at = (
            datetime.now(
                timezone.utc
            )
        )

        db.commit()

        db.refresh(
            prediction
        )

        return prediction

    @staticmethod
    def mark_failed(
        db: Session,
        prediction: Prediction
    ) -> Prediction:

        prediction.status = (
            "failed"
        )

        prediction.completed_at = (
            datetime.now(
                timezone.utc
            )
        )

        db.commit()

        db.refresh(
            prediction
        )

        return prediction