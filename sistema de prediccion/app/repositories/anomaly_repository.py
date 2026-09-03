from datetime import (
    datetime,
    timezone,
)

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.anomaly import Anomaly


class AnomalyRepository:

    @staticmethod
    def create(
        db: Session,
        anomaly_type: str,
        method: str,
        business_series_id: int | None = None,
        model_id: int | None = None,
        prediction_id: int | None = None,
        prediction_result_id: int | None = None,
        observed_value: float | None = None,
        expected_value: float | None = None,
        deviation: float | None = None,
        score: float | None = None,
        severity: str = "medium",
        status: str = "open",
        details: dict | None = None
    ) -> Anomaly:

        anomaly = Anomaly(
            business_series_id=(
                business_series_id
            ),
            model_id=model_id,
            prediction_id=prediction_id,
            prediction_result_id=(
                prediction_result_id
            ),
            anomaly_type=anomaly_type,
            method=method,
            observed_value=observed_value,
            expected_value=expected_value,
            deviation=deviation,
            score=score,
            severity=severity,
            status=status,
            details=details
        )

        db.add(anomaly)
        db.commit()
        db.refresh(anomaly)

        return anomaly

    @staticmethod
    def get_by_id(
        db: Session,
        anomaly_id: int
    ) -> Anomaly | None:

        return db.get(
            Anomaly,
            anomaly_id
        )

    @staticmethod
    def get_existing(
        db: Session,
        prediction_result_id: int,
        anomaly_type: str,
        method: str
    ) -> Anomaly | None:

        statement = (
            select(Anomaly)
            .where(
                Anomaly.prediction_result_id
                == prediction_result_id,
                Anomaly.anomaly_type
                == anomaly_type,
                Anomaly.method
                == method
            )
            .limit(1)
        )

        return db.scalar(statement)

    @staticmethod
    def get_all(
        db: Session,
        business_series_id: int | None = None,
        model_id: int | None = None,
        status: str | None = None,
        limit: int = 100
    ) -> list[Anomaly]:

        statement = (
            select(Anomaly)
            .order_by(
                Anomaly.detected_at.desc()
            )
        )

        if business_series_id is not None:

            statement = statement.where(
                Anomaly.business_series_id
                == business_series_id
            )

        if model_id is not None:

            statement = statement.where(
                Anomaly.model_id
                == model_id
            )

        if status:

            statement = statement.where(
                Anomaly.status == status
            )

        statement = statement.limit(limit)

        return list(
            db.scalars(
                statement
            ).all()
        )

    @staticmethod
    def get_by_prediction(
        db: Session,
        prediction_id: int
    ) -> list[Anomaly]:

        statement = (
            select(Anomaly)
            .where(
                Anomaly.prediction_id
                == prediction_id
            )
            .order_by(
                Anomaly.detected_at.desc()
            )
        )

        return list(
            db.scalars(
                statement
            ).all()
        )

    @staticmethod
    def resolve(
        db: Session,
        anomaly: Anomaly
    ) -> Anomaly:

        anomaly.status = "resolved"

        anomaly.resolved_at = (
            datetime.now(
                timezone.utc
            )
        )

        db.commit()
        db.refresh(anomaly)

        return anomaly

    @staticmethod
    def reopen(
        db: Session,
        anomaly: Anomaly
    ) -> Anomaly:

        anomaly.status = "open"
        anomaly.resolved_at = None

        db.commit()
        db.refresh(anomaly)

        return anomaly