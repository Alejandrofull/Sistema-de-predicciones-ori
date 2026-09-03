from sqlalchemy import (
    func,
    select,
)

from sqlalchemy.orm import Session

from app.models.model import MLModel

from app.models.model_version import (
    ModelVersion,
)


class ModelVersionRepository:

    @staticmethod
    def create(
        db: Session,
        model_id: int,
        version_number: int,
        parameters: dict | None,
        feature_config: dict | None,
        artifact_path: str | None,
        is_active: bool = False
    ) -> ModelVersion:

        version = ModelVersion(
            model_id=model_id,
            version_number=version_number,
            parameters=parameters,
            feature_config=feature_config,
            artifact_path=artifact_path,
            is_active=is_active
        )

        db.add(version)
        db.commit()
        db.refresh(version)

        return version

    @staticmethod
    def get_by_id(
        db: Session,
        version_id: int
    ) -> ModelVersion | None:

        return db.get(
            ModelVersion,
            version_id
        )

    @staticmethod
    def get_by_model(
        db: Session,
        model_id: int
    ) -> list[ModelVersion]:

        statement = (
            select(ModelVersion)
            .where(
                ModelVersion.model_id
                == model_id
            )
            .order_by(
                ModelVersion.version_number.desc()
            )
        )

        return list(
            db.scalars(
                statement
            ).all()
        )

    @staticmethod
    def get_latest(
        db: Session,
        model_id: int
    ) -> ModelVersion | None:

        statement = (
            select(ModelVersion)
            .where(
                ModelVersion.model_id
                == model_id
            )
            .order_by(
                ModelVersion.version_number.desc()
            )
            .limit(1)
        )

        return db.scalar(
            statement
        )

    @staticmethod
    def get_active_by_model(
        db: Session,
        model_id: int
    ) -> ModelVersion | None:

        statement = (
            select(ModelVersion)
            .where(
                ModelVersion.model_id
                == model_id,
                ModelVersion.is_active.is_(
                    True
                )
            )
            .order_by(
                ModelVersion.version_number.desc()
            )
            .limit(1)
        )

        return db.scalar(
            statement
        )

    @staticmethod
    def get_next_version_number(
        db: Session,
        model_id: int
    ) -> int:

        current_max = db.scalar(
            select(
                func.max(
                    ModelVersion.version_number
                )
            )
            .where(
                ModelVersion.model_id
                == model_id
            )
        )

        if current_max is None:
            return 1

        return int(
            current_max
        ) + 1

    @staticmethod
    def deactivate_for_business_series(
        db: Session,
        business_series_id: int | None
    ) -> None:

        statement = (
            select(ModelVersion)
            .join(
                MLModel,
                MLModel.id
                == ModelVersion.model_id
            )
            .where(
                ModelVersion.is_active.is_(
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

        versions = list(
            db.scalars(
                statement
            ).all()
        )

        for version in versions:
            version.is_active = False

        db.commit()

    @staticmethod
    def set_active(
        db: Session,
        version: ModelVersion,
        active: bool
    ) -> ModelVersion:

        version.is_active = active

        db.commit()
        db.refresh(version)

        return version