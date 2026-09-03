from sqlalchemy import (
    select,
)

from sqlalchemy.orm import Session

from app.models.model_evaluations import (
    ModelEvaluation,
)


class ModelEvaluationRepository:

    @staticmethod
    def create(
        db: Session,
        model_id: int,
        model_version_id: int | None,
        training_id: int | None,
        dataset_id: int,
        evaluation_type: str = "backtest",
        mae: float | None = None,
        mse: float | None = None,
        rmse: float | None = None,
        mape: float | None = None,
        smape: float | None = None,
        r2: float | None = None,
        training_time_seconds: float | None = None,
        prediction_time_seconds: float | None = None,
        score: float | None = None,
        ranking_position: int | None = None,
        is_best_model: bool = False,
        evaluation_config: dict | None = None,
        notes: str | None = None
    ) -> ModelEvaluation:

        evaluation = ModelEvaluation(
            model_id=model_id,
            model_version_id=(
                model_version_id
            ),
            training_id=(
                training_id
            ),
            dataset_id=(
                dataset_id
            ),
            evaluation_type=(
                evaluation_type
            ),
            mae=mae,
            mse=mse,
            rmse=rmse,
            mape=mape,
            smape=smape,
            r2=r2,
            training_time_seconds=(
                training_time_seconds
            ),
            prediction_time_seconds=(
                prediction_time_seconds
            ),
            score=score,
            ranking_position=(
                ranking_position
            ),
            is_best_model=(
                is_best_model
            ),
            evaluation_config=(
                evaluation_config
            ),
            notes=notes
        )

        db.add(
            evaluation
        )

        db.commit()

        db.refresh(
            evaluation
        )

        return evaluation

    @staticmethod
    def get_by_id(
        db: Session,
        evaluation_id: int
    ) -> ModelEvaluation | None:

        return db.get(
            ModelEvaluation,
            evaluation_id
        )

    @staticmethod
    def get_by_model(
        db: Session,
        model_id: int
    ) -> list[ModelEvaluation]:

        statement = (
            select(
                ModelEvaluation
            )
            .where(
                ModelEvaluation.model_id
                == model_id
            )
            .order_by(
                ModelEvaluation.evaluated_at.desc()
            )
        )

        return list(
            db.scalars(
                statement
            ).all()
        )

    @staticmethod
    def get_latest_by_model(
        db: Session,
        model_id: int
    ) -> ModelEvaluation | None:

        statement = (
            select(
                ModelEvaluation
            )
            .where(
                ModelEvaluation.model_id
                == model_id
            )
            .order_by(
                ModelEvaluation.evaluated_at.desc()
            )
            .limit(
                1
            )
        )

        return db.scalar(
            statement
        )

    @staticmethod
    def get_latest_by_model_version(
        db: Session,
        model_version_id: int
    ) -> ModelEvaluation | None:

        statement = (
            select(
                ModelEvaluation
            )
            .where(
                ModelEvaluation.model_version_id
                == model_version_id
            )
            .order_by(
                ModelEvaluation.evaluated_at.desc()
            )
            .limit(
                1
            )
        )

        return db.scalar(
            statement
        )

    @staticmethod
    def get_by_training(
        db: Session,
        training_id: int
    ) -> list[ModelEvaluation]:

        statement = (
            select(
                ModelEvaluation
            )
            .where(
                ModelEvaluation.training_id
                == training_id
            )
            .order_by(
                ModelEvaluation.ranking_position.asc()
            )
        )

        return list(
            db.scalars(
                statement
            ).all()
        )

    @staticmethod
    def update_ranking(
        db: Session,
        evaluation: ModelEvaluation,
        ranking_position: int,
        is_best_model: bool
    ) -> ModelEvaluation:

        evaluation.ranking_position = (
            ranking_position
        )

        evaluation.is_best_model = (
            is_best_model
        )

        db.commit()

        db.refresh(
            evaluation
        )

        return evaluation