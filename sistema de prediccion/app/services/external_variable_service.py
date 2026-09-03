from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories.external_variable_repository import (
    ExternalVariableRepository,
)

from app.repositories.external_variable_value_repository import (
    ExternalVariableValueRepository,
)


class ExternalVariableService:

    @staticmethod
    def create_variable(
        db: Session,
        name: str,
        variable_type: str,
        source_type: str,
        description: str | None,
        unit: str | None,
        is_active: bool
    ):

        existing = (
            ExternalVariableRepository
            .get_by_name(
                db,
                name
            )
        )

        if existing:

            raise HTTPException(
                status_code=409,
                detail=(
                    "Ya existe una variable "
                    "externa con ese nombre"
                )
            )

        return (
            ExternalVariableRepository.create(
                db=db,
                name=name,
                variable_type=variable_type,
                source_type=source_type,
                description=description,
                unit=unit,
                is_active=is_active
            )
        )

    @staticmethod
    def update_variable(
        db: Session,
        variable_id: int,
        name: str,
        variable_type: str,
        source_type: str,
        description: str | None,
        unit: str | None,
        is_active: bool
    ):

        variable = (
            ExternalVariableRepository
            .get_by_id(
                db,
                variable_id
            )
        )

        if not variable:

            raise HTTPException(
                status_code=404,
                detail=(
                    "Variable externa "
                    "no encontrada"
                )
            )

        existing = (
            ExternalVariableRepository
            .get_by_name(
                db,
                name
            )
        )

        if (
            existing
            and existing.id
            != variable.id
        ):

            raise HTTPException(
                status_code=409,
                detail=(
                    "Ya existe otra variable "
                    "externa con ese nombre"
                )
            )

        return (
            ExternalVariableRepository.update(
                db=db,
                variable=variable,
                name=name,
                variable_type=variable_type,
                source_type=source_type,
                description=description,
                unit=unit,
                is_active=is_active
            )
        )

    @staticmethod
    def set_status(
        db: Session,
        variable_id: int,
        is_active: bool
    ):

        variable = (
            ExternalVariableRepository
            .get_by_id(
                db,
                variable_id
            )
        )

        if not variable:

            raise HTTPException(
                status_code=404,
                detail=(
                    "Variable externa "
                    "no encontrada"
                )
            )

        return (
            ExternalVariableRepository.set_active(
                db=db,
                variable=variable,
                is_active=is_active
            )
        )

    @staticmethod
    def create_value(
        db: Session,
        variable_id: int,
        reference_date,
        numeric_value: float | None,
        text_value: str | None,
        business_key: str | None
    ):

        variable = (
            ExternalVariableRepository
            .get_by_id(
                db,
                variable_id
            )
        )

        if not variable:

            raise HTTPException(
                status_code=404,
                detail=(
                    "Variable externa "
                    "no encontrada"
                )
            )

        ExternalVariableService._validate_value(
            variable=variable,
            numeric_value=numeric_value,
            text_value=text_value
        )

        return (
            ExternalVariableValueRepository
            .create(
                db=db,
                variable_id=variable.id,
                reference_date=reference_date,
                numeric_value=numeric_value,
                text_value=text_value,
                business_key=business_key
            )
        )

    @staticmethod
    def create_values(
        db: Session,
        variable_id: int,
        values: list
    ):

        variable = (
            ExternalVariableRepository
            .get_by_id(
                db,
                variable_id
            )
        )

        if not variable:

            raise HTTPException(
                status_code=404,
                detail=(
                    "Variable externa "
                    "no encontrada"
                )
            )

        normalized = []

        for value in values:

            ExternalVariableService._validate_value(
                variable=variable,
                numeric_value=(
                    value.numeric_value
                ),
                text_value=(
                    value.text_value
                )
            )

            normalized.append(
                {
                    "reference_date": (
                        value.reference_date
                    ),
                    "numeric_value": (
                        value.numeric_value
                    ),
                    "text_value": (
                        value.text_value
                    ),
                    "business_key": (
                        value.business_key
                    )
                }
            )

        return (
            ExternalVariableValueRepository
            .create_many(
                db=db,
                variable_id=(
                    variable.id
                ),
                values=normalized
            )
        )

    @staticmethod
    def _validate_value(
        variable,
        numeric_value: float | None,
        text_value: str | None
    ) -> None:

        variable_type = (
            variable.variable_type
            .strip()
            .lower()
        )

        if (
            variable_type
            in {
                "numeric",
                "boolean",
            }
            and numeric_value is None
        ):

            raise HTTPException(
                status_code=400,
                detail=(
                    f"La variable '{variable.name}' "
                    "requiere numeric_value"
                )
            )

        if (
            variable_type == "boolean"
            and numeric_value
            not in {
                0,
                0.0,
                1,
                1.0,
            }
        ):

            raise HTTPException(
                status_code=400,
                detail=(
                    "Una variable boolean "
                    "debe usar 0 o 1"
                )
            )

        if (
            variable_type
            in {
                "categorical",
                "text",
            }
            and text_value is None
        ):

            raise HTTPException(
                status_code=400,
                detail=(
                    f"La variable '{variable.name}' "
                    "requiere text_value"
                )
            )