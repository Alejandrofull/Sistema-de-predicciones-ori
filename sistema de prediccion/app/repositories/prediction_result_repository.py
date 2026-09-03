from datetime import date

from sqlalchemy import (
    select,
)

from sqlalchemy.orm import Session

from app.models.prediction import (
    Prediction,
    PredictionResult,
)


class PredictionResultRepository:

    @staticmethod
    def create(
        db: Session,
        prediction_id: int,
        prediction_date: date,
        predicted_value: float,
        actual_value: float | None = None,
        lower_bound: float | None = None,
        upper_bound: float | None = None,
        commit: bool = True
    ) -> PredictionResult:

        result = PredictionResult(
            prediction_id=prediction_id,
            prediction_date=prediction_date,
            predicted_value=predicted_value,
            actual_value=actual_value,
            lower_bound=lower_bound,
            upper_bound=upper_bound
        )

        db.add(
            result
        )

        if commit:

            db.commit()

            db.refresh(
                result
            )

        return result

    @staticmethod
    def create_many(
        db: Session,
        prediction_id: int,
        values: list[dict]
    ) -> list[PredictionResult]:

        results = []

        for value in values:

            result = PredictionResult(
                prediction_id=(
                    prediction_id
                ),
                prediction_date=(
                    value[
                        "prediction_date"
                    ]
                ),
                predicted_value=float(
                    value[
                        "predicted_value"
                    ]
                ),
                actual_value=(
                    value.get(
                        "actual_value"
                    )
                ),
                lower_bound=(
                    value.get(
                        "lower_bound"
                    )
                ),
                upper_bound=(
                    value.get(
                        "upper_bound"
                    )
                )
            )

            db.add(
                result
            )

            results.append(
                result
            )

        db.commit()

        for result in results:

            db.refresh(
                result
            )

        return results

    @staticmethod
    def get_by_prediction(
        db: Session,
        prediction_id: int
    ) -> list[PredictionResult]:

        statement = (
            select(
                PredictionResult
            )
            .where(
                PredictionResult.prediction_id
                == prediction_id
            )
            .order_by(
                PredictionResult.prediction_date.asc()
            )
        )

        return list(
            db.scalars(
                statement
            ).all()
        )

    @staticmethod
    def get_with_actual_by_prediction(
        db: Session,
        prediction_id: int
    ) -> list[PredictionResult]:

        statement = (
            select(
                PredictionResult
            )
            .where(
                PredictionResult.prediction_id
                == prediction_id,
                PredictionResult.actual_value.is_not(
                    None
                )
            )
            .order_by(
                PredictionResult.prediction_date.asc()
            )
        )

        return list(
            db.scalars(
                statement
            ).all()
        )

    @staticmethod
    def get_with_actual_by_model(
        db: Session,
        model_id: int,
        limit: int | None = None
    ) -> list[PredictionResult]:

        statement = (
            select(
                PredictionResult
            )
            .join(
                Prediction,
                Prediction.id
                == PredictionResult.prediction_id
            )
            .where(
                Prediction.model_id
                == model_id,
                PredictionResult.actual_value.is_not(
                    None
                )
            )
            .order_by(
                PredictionResult.prediction_date.desc()
            )
        )

        if limit:

            statement = (
                statement.limit(
                    limit
                )
            )

        results = list(
            db.scalars(
                statement
            ).all()
        )

        return sorted(
            results,
            key=lambda item: (
                item.prediction_date
            )
        )

    @staticmethod
    def get_with_actual_by_business_series(
        db: Session,
        business_series_id: int,
        limit: int | None = None
    ) -> list[PredictionResult]:

        statement = (
            select(
                PredictionResult
            )
            .join(
                Prediction,
                Prediction.id
                == PredictionResult.prediction_id
            )
            .where(
                Prediction.business_series_id
                == business_series_id,
                PredictionResult.actual_value.is_not(
                    None
                )
            )
            .order_by(
                PredictionResult.prediction_date.desc()
            )
        )

        if limit:

            statement = (
                statement.limit(
                    limit
                )
            )

        results = list(
            db.scalars(
                statement
            ).all()
        )

        return sorted(
            results,
            key=lambda item: (
                item.prediction_date
            )
        )

    @staticmethod
    def get_by_id(
        db: Session,
        result_id: int
    ) -> PredictionResult | None:

        return db.get(
            PredictionResult,
            result_id
        )

    @staticmethod
    def update_actual_value(
        db: Session,
        result: PredictionResult,
        actual_value: float
    ) -> PredictionResult:

        result.actual_value = float(
            actual_value
        )

        db.commit()

        db.refresh(
            result
        )

        return result