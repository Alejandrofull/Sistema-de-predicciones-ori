from datetime import datetime

from sqlalchemy import (
    or_,
    select,
)

from sqlalchemy.orm import Session

from app.models.external_variable_values import (
    ExternalVariableValue,
)


class ExternalVariableValueRepository:

    @staticmethod
    def create(
        db: Session,
        variable_id: int,
        reference_date: datetime,
        numeric_value: float | None = None,
        text_value: str | None = None,
        business_key: str | None = None
    ) -> ExternalVariableValue:

        value = ExternalVariableValue(
            variable_id=variable_id,
            reference_date=reference_date,
            numeric_value=numeric_value,
            text_value=text_value,
            business_key=business_key
        )

        db.add(value)
        db.commit()
        db.refresh(value)

        return value

    @staticmethod
    def create_many(
        db: Session,
        variable_id: int,
        values: list[dict]
    ) -> list[ExternalVariableValue]:

        records = []

        for item in values:

            record = ExternalVariableValue(
                variable_id=variable_id,
                reference_date=(
                    item["reference_date"]
                ),
                numeric_value=(
                    item.get(
                        "numeric_value"
                    )
                ),
                text_value=(
                    item.get(
                        "text_value"
                    )
                ),
                business_key=(
                    item.get(
                        "business_key"
                    )
                )
            )

            db.add(record)
            records.append(record)

        db.commit()

        for record in records:
            db.refresh(record)

        return records

    @staticmethod
    def get_by_id(
        db: Session,
        value_id: int
    ) -> ExternalVariableValue | None:

        return db.get(
            ExternalVariableValue,
            value_id
        )

    @staticmethod
    def get_by_variable(
        db: Session,
        variable_id: int,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        business_key: str | None = None,
        include_global: bool = True
    ) -> list[ExternalVariableValue]:

        statement = (
            select(ExternalVariableValue)
            .where(
                ExternalVariableValue.variable_id
                == variable_id
            )
        )

        if start_date is not None:

            statement = statement.where(
                ExternalVariableValue.reference_date
                >= start_date
            )

        if end_date is not None:

            statement = statement.where(
                ExternalVariableValue.reference_date
                <= end_date
            )

        if business_key is not None:

            if include_global:

                statement = statement.where(
                    or_(
                        ExternalVariableValue.business_key
                        == business_key,
                        ExternalVariableValue.business_key
                        .is_(None)
                    )
                )

            else:

                statement = statement.where(
                    ExternalVariableValue.business_key
                    == business_key
                )

        elif not include_global:

            statement = statement.where(
                ExternalVariableValue.business_key
                .is_not(None)
            )

        statement = statement.order_by(
            ExternalVariableValue.reference_date.asc(),
            ExternalVariableValue.id.asc()
        )

        return list(
            db.scalars(
                statement
            ).all()
        )

    @staticmethod
    def delete(
        db: Session,
        value: ExternalVariableValue
    ) -> None:

        db.delete(value)
        db.commit()