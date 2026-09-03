from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.business_series import BusinessSeries


class BusinessSeriesRepository:

    @staticmethod
    def create(
        db: Session,
        external_entity_id: str,
        entity_type: str,
        name: str | None = None,
        dimensions: dict | None = None,
        is_active: bool = True
    ) -> BusinessSeries:

        business_series = BusinessSeries(
            external_entity_id=external_entity_id,
            entity_type=entity_type,
            name=name,
            dimensions=dimensions,
            is_active=is_active
        )

        db.add(business_series)
        db.commit()
        db.refresh(business_series)

        return business_series

    @staticmethod
    def get_by_id(
        db: Session,
        business_series_id: int
    ) -> BusinessSeries | None:

        return db.get(
            BusinessSeries,
            business_series_id
        )

    @staticmethod
    def get_by_external_entity_id(
        db: Session,
        external_entity_id: str,
        entity_type: str | None = None
    ) -> BusinessSeries | None:

        statement = (
            select(BusinessSeries)
            .where(
                BusinessSeries.external_entity_id
                == external_entity_id
            )
        )

        if entity_type:
            statement = statement.where(
                BusinessSeries.entity_type
                == entity_type
            )

        statement = (
            statement
            .order_by(
                BusinessSeries.id.asc()
            )
            .limit(1)
        )

        return db.scalar(
            statement
        )

    @staticmethod
    def get_all(
        db: Session,
        include_inactive: bool = False
    ) -> list[BusinessSeries]:

        statement = (
            select(BusinessSeries)
            .order_by(
                BusinessSeries.name.asc(),
                BusinessSeries.id.asc()
            )
        )

        if not include_inactive:
            statement = statement.where(
                BusinessSeries.is_active.is_(
                    True
                )
            )

        return list(
            db.scalars(
                statement
            ).all()
        )

    @staticmethod
    def get_by_entity_type(
        db: Session,
        entity_type: str,
        include_inactive: bool = False
    ) -> list[BusinessSeries]:

        statement = (
            select(BusinessSeries)
            .where(
                BusinessSeries.entity_type
                == entity_type
            )
            .order_by(
                BusinessSeries.name.asc(),
                BusinessSeries.id.asc()
            )
        )

        if not include_inactive:
            statement = statement.where(
                BusinessSeries.is_active.is_(
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
        business_series: BusinessSeries,
        external_entity_id: str,
        entity_type: str,
        name: str | None,
        dimensions: dict | None,
        is_active: bool
    ) -> BusinessSeries:

        business_series.external_entity_id = (
            external_entity_id
        )

        business_series.entity_type = (
            entity_type
        )

        business_series.name = name

        business_series.dimensions = (
            dimensions
        )

        business_series.is_active = (
            is_active
        )

        db.commit()
        db.refresh(
            business_series
        )

        return business_series

    @staticmethod
    def set_active(
        db: Session,
        business_series: BusinessSeries,
        is_active: bool
    ) -> BusinessSeries:

        business_series.is_active = (
            is_active
        )

        db.commit()
        db.refresh(
            business_series
        )

        return business_series

    @staticmethod
    def delete(
        db: Session,
        business_series: BusinessSeries
    ) -> None:

        db.delete(
            business_series
        )

        db.commit()