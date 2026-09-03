from sqlalchemy import (
    select,
)

from sqlalchemy.orm import Session

from app.models.model import MLModel


class ModelRepository:

    @staticmethod
    def create(
        db: Session,
        name: str,
        model_type: str,
        business_series_id: int | None = None,
        version: str | None = None,
        metric_value: float | None = None,
        active: bool = False
    ) -> MLModel:

        model = MLModel(
            business_series_id=(
                business_series_id
            ),
            name=name,
            model_type=model_type,
            version=version,
            metric_value=metric_value,
            active=active
        )

        db.add(model)
        db.commit()
        db.refresh(model)

        return model

    @staticmethod
    def get_or_create(
        db: Session,
        name: str,
        model_type: str,
        business_series_id: int | None
    ) -> MLModel:

        existing = (
            ModelRepository
            .get_by_series_and_type(
                db=db,
                business_series_id=(
                    business_series_id
                ),
                model_type=model_type
            )
        )

        if existing:
            return existing

        return (
            ModelRepository.create(
                db=db,
                name=name,
                model_type=model_type,
                business_series_id=(
                    business_series_id
                ),
                active=False
            )
        )

    @staticmethod
    def get_by_id(
        db: Session,
        model_id: int
    ) -> MLModel | None:

        return db.get(
            MLModel,
            model_id
        )

    @staticmethod
    def get_by_series_and_type(
        db: Session,
        business_series_id: int | None,
        model_type: str
    ) -> MLModel | None:

        statement = (
            select(MLModel)
            .where(
                MLModel.model_type
                == model_type
            )
        )

        if business_series_id is None:

            statement = statement.where(
                MLModel.business_series_id.is_(
                    None
                )
            )

        else:

            statement = statement.where(
                MLModel.business_series_id
                == business_series_id
            )

        statement = (
            statement
            .order_by(
                MLModel.id.asc()
            )
            .limit(1)
        )

        return db.scalar(
            statement
        )

    @staticmethod
    def get_all(
        db: Session
    ) -> list[MLModel]:

        statement = (
            select(MLModel)
            .order_by(
                MLModel.created_at.desc()
            )
        )

        return list(
            db.scalars(
                statement
            ).all()
        )

    @staticmethod
    def get_by_business_series(
        db: Session,
        business_series_id: int
    ) -> list[MLModel]:

        statement = (
            select(MLModel)
            .where(
                MLModel.business_series_id
                == business_series_id
            )
            .order_by(
                MLModel.created_at.desc()
            )
        )

        return list(
            db.scalars(
                statement
            ).all()
        )

    @staticmethod
    def get_active_global(
        db: Session
    ) -> MLModel | None:

        statement = (
            select(MLModel)
            .where(
                MLModel.active.is_(True),
                MLModel.business_series_id.is_(
                    None
                )
            )
            .order_by(
                MLModel.created_at.desc()
            )
            .limit(1)
        )

        return db.scalar(
            statement
        )

    @staticmethod
    def get_active_by_business_series(
        db: Session,
        business_series_id: int
    ) -> MLModel | None:

        statement = (
            select(MLModel)
            .where(
                MLModel.business_series_id
                == business_series_id,
                MLModel.active.is_(
                    True
                )
            )
            .order_by(
                MLModel.created_at.desc()
            )
            .limit(1)
        )

        return db.scalar(
            statement
        )

    @staticmethod
    def update_training_result(
        db: Session,
        model: MLModel,
        version: str,
        metric_value: float
    ) -> MLModel:

        model.version = version

        model.metric_value = (
            metric_value
        )

        db.commit()
        db.refresh(model)

        return model

    @staticmethod
    def deactivate_by_business_series(
        db: Session,
        business_series_id: int | None
    ) -> None:

        statement = (
            select(MLModel)
            .where(
                MLModel.active.is_(
                    True
                )
            )
        )

        if business_series_id is None:

            statement = statement.where(
                MLModel.business_series_id.is_(
                    None
                )
            )

        else:

            statement = statement.where(
                MLModel.business_series_id
                == business_series_id
            )

        models = list(
            db.scalars(
                statement
            ).all()
        )

        for model in models:
            model.active = False

        db.commit()

    @staticmethod
    def set_active(
        db: Session,
        model: MLModel,
        active: bool
    ) -> MLModel:

        model.active = active

        db.commit()
        db.refresh(model)

        return model