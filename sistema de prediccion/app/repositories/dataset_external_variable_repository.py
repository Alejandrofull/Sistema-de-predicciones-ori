from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.dataset_external_variables import (
    DatasetExternalVariable,
)

from app.models.external_variable import (
    ExternalVariable,
)


class DatasetExternalVariableRepository:

    @staticmethod
    def attach(
        db: Session,
        dataset_id: int,
        external_variable_id: int
    ) -> DatasetExternalVariable:

        existing = (
            DatasetExternalVariableRepository
            .get_link(
                db=db,
                dataset_id=dataset_id,
                external_variable_id=(
                    external_variable_id
                )
            )
        )

        if existing:
            return existing

        link = DatasetExternalVariable(
            dataset_id=dataset_id,
            external_variable_id=(
                external_variable_id
            )
        )

        db.add(link)
        db.commit()
        db.refresh(link)

        return link

    @staticmethod
    def get_link(
        db: Session,
        dataset_id: int,
        external_variable_id: int
    ) -> DatasetExternalVariable | None:

        statement = (
            select(
                DatasetExternalVariable
            )
            .where(
                DatasetExternalVariable.dataset_id
                == dataset_id,
                DatasetExternalVariable.external_variable_id
                == external_variable_id
            )
            .limit(1)
        )

        return db.scalar(statement)

    @staticmethod
    def get_links_by_dataset(
        db: Session,
        dataset_id: int
    ) -> list[DatasetExternalVariable]:

        statement = (
            select(
                DatasetExternalVariable
            )
            .where(
                DatasetExternalVariable.dataset_id
                == dataset_id
            )
            .order_by(
                DatasetExternalVariable.id.asc()
            )
        )

        return list(
            db.scalars(
                statement
            ).all()
        )

    @staticmethod
    def get_variables_by_dataset(
        db: Session,
        dataset_id: int
    ) -> list[ExternalVariable]:

        statement = (
            select(ExternalVariable)
            .join(
                DatasetExternalVariable,
                DatasetExternalVariable.external_variable_id
                == ExternalVariable.id
            )
            .where(
                DatasetExternalVariable.dataset_id
                == dataset_id
            )
            .order_by(
                ExternalVariable.name.asc()
            )
        )

        return list(
            db.scalars(
                statement
            ).all()
        )

    @staticmethod
    def detach(
        db: Session,
        link: DatasetExternalVariable
    ) -> None:

        db.delete(link)
        db.commit()