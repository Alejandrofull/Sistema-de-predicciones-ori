from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.inventory_observation import (
    InventoryObservation,
)


class InventoryObservationRepository:

    @staticmethod
    def create(
        db: Session,
        business_series_id: int,
        user_id: int | None,
        observation_date: date,
        phase: str,
        opening_stock: float,
        replenishment_quantity: float,
        actual_demand: float,
        closing_stock: float,
        predicted_demand: float | None,
        source_type: str
    ) -> InventoryObservation:

        observation = InventoryObservation(
            business_series_id=business_series_id,
            user_id=user_id,
            observation_date=observation_date,
            phase=phase,
            opening_stock=opening_stock,
            replenishment_quantity=(
                replenishment_quantity
            ),
            actual_demand=actual_demand,
            closing_stock=closing_stock,
            predicted_demand=predicted_demand,
            source_type=source_type
        )

        db.add(observation)
        db.commit()
        db.refresh(observation)

        return observation

    @staticmethod
    def get_by_id(
        db: Session,
        observation_id: int
    ) -> InventoryObservation | None:

        return db.get(
            InventoryObservation,
            observation_id
        )

    @staticmethod
    def get_existing(
        db: Session,
        business_series_id: int,
        observation_date: date,
        phase: str
    ) -> InventoryObservation | None:

        statement = (
            select(
                InventoryObservation
            )
            .where(
                InventoryObservation.business_series_id
                == business_series_id,
                InventoryObservation.observation_date
                == observation_date,
                InventoryObservation.phase
                == phase
            )
            .limit(1)
        )

        return db.scalar(
            statement
        )

    @staticmethod
    def get_all(
        db: Session,
        phase: str | None = None,
        business_series_id: int | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        limit: int = 1000
    ) -> list[InventoryObservation]:

        statement = (
            select(
                InventoryObservation
            )
            .order_by(
                InventoryObservation
                .observation_date
                .asc(),
                InventoryObservation.id.asc()
            )
        )

        if phase is not None:

            statement = statement.where(
                InventoryObservation.phase
                == phase
            )

        if business_series_id is not None:

            statement = statement.where(
                InventoryObservation
                .business_series_id
                == business_series_id
            )

        if start_date is not None:

            statement = statement.where(
                InventoryObservation
                .observation_date
                >= start_date
            )

        if end_date is not None:

            statement = statement.where(
                InventoryObservation
                .observation_date
                <= end_date
            )

        statement = statement.limit(
            limit
        )

        return list(
            db.scalars(
                statement
            ).all()
        )

    @staticmethod
    def delete(
        db: Session,
        observation: InventoryObservation
    ) -> None:

        db.delete(
            observation
        )

        db.commit()