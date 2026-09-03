from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.external_variable import (
    ExternalVariable,
)


class ExternalVariableRepository:

    @staticmethod
    def create(
        db: Session,
        name: str,
        variable_type: str,
        source_type: str,
        description: str | None = None,
        unit: str | None = None,
        is_active: bool = True
    ) -> ExternalVariable:

        variable = ExternalVariable(
            name=name,
            variable_type=variable_type,
            source_type=source_type,
            description=description,
            unit=unit,
            is_active=is_active
        )

        db.add(variable)
        db.commit()
        db.refresh(variable)

        return variable

    @staticmethod
    def get_by_id(
        db: Session,
        variable_id: int
    ) -> ExternalVariable | None:

        return db.get(
            ExternalVariable,
            variable_id
        )

    @staticmethod
    def get_by_name(
        db: Session,
        name: str
    ) -> ExternalVariable | None:

        statement = (
            select(ExternalVariable)
            .where(
                ExternalVariable.name == name
            )
            .limit(1)
        )

        return db.scalar(statement)

    @staticmethod
    def get_all(
        db: Session,
        include_inactive: bool = False
    ) -> list[ExternalVariable]:

        statement = (
            select(ExternalVariable)
            .order_by(
                ExternalVariable.name.asc()
            )
        )

        if not include_inactive:

            statement = statement.where(
                ExternalVariable.is_active.is_(
                    True
                )
            )

        return list(
            db.scalars(
                statement
            ).all()
        )

    @staticmethod
    def update(
        db: Session,
        variable: ExternalVariable,
        name: str,
        variable_type: str,
        source_type: str,
        description: str | None,
        unit: str | None,
        is_active: bool
    ) -> ExternalVariable:

        variable.name = name
        variable.variable_type = variable_type
        variable.source_type = source_type
        variable.description = description
        variable.unit = unit
        variable.is_active = is_active

        db.commit()
        db.refresh(variable)

        return variable

    @staticmethod
    def set_active(
        db: Session,
        variable: ExternalVariable,
        is_active: bool
    ) -> ExternalVariable:

        variable.is_active = is_active

        db.commit()
        db.refresh(variable)

        return variable

    @staticmethod
    def delete(
        db: Session,
        variable: ExternalVariable
    ) -> None:

        db.delete(variable)
        db.commit()