from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories.business_series_repository import (
    BusinessSeriesRepository,
)


class BusinessSeriesService:

    @staticmethod
    def create(
        db: Session,
        external_entity_id: str,
        entity_type: str,
        name: str | None,
        dimensions: dict | None,
        is_active: bool
    ):

        existing = (
            BusinessSeriesRepository
            .get_by_external_entity_id(
                db=db,
                external_entity_id=(
                    external_entity_id
                ),
                entity_type=(
                    entity_type
                )
            )
        )

        if existing:
            raise HTTPException(
                status_code=409,
                detail=(
                    "Ya existe una serie "
                    "de negocio con el mismo "
                    "external_entity_id y "
                    "entity_type"
                )
            )

        return (
            BusinessSeriesRepository.create(
                db=db,
                external_entity_id=(
                    external_entity_id
                ),
                entity_type=entity_type,
                name=name,
                dimensions=dimensions,
                is_active=is_active
            )
        )

    @staticmethod
    def update(
        db: Session,
        business_series_id: int,
        external_entity_id: str,
        entity_type: str,
        name: str | None,
        dimensions: dict | None,
        is_active: bool
    ):

        business_series = (
            BusinessSeriesRepository
            .get_by_id(
                db,
                business_series_id
            )
        )

        if not business_series:
            raise HTTPException(
                status_code=404,
                detail=(
                    "Serie de negocio "
                    "no encontrada"
                )
            )

        existing = (
            BusinessSeriesRepository
            .get_by_external_entity_id(
                db=db,
                external_entity_id=(
                    external_entity_id
                ),
                entity_type=(
                    entity_type
                )
            )
        )

        if (
            existing
            and existing.id
            != business_series.id
        ):
            raise HTTPException(
                status_code=409,
                detail=(
                    "Ya existe otra serie "
                    "con el mismo identificador"
                )
            )

        return (
            BusinessSeriesRepository.update(
                db=db,
                business_series=(
                    business_series
                ),
                external_entity_id=(
                    external_entity_id
                ),
                entity_type=entity_type,
                name=name,
                dimensions=dimensions,
                is_active=is_active
            )
        )

    @staticmethod
    def set_status(
        db: Session,
        business_series_id: int,
        is_active: bool
    ):

        business_series = (
            BusinessSeriesRepository
            .get_by_id(
                db,
                business_series_id
            )
        )

        if not business_series:
            raise HTTPException(
                status_code=404,
                detail=(
                    "Serie de negocio "
                    "no encontrada"
                )
            )

        return (
            BusinessSeriesRepository
            .set_active(
                db=db,
                business_series=(
                    business_series
                ),
                is_active=is_active
            )
        )

    @staticmethod
    def delete(
        db: Session,
        business_series_id: int
    ) -> None:

        business_series = (
            BusinessSeriesRepository
            .get_by_id(
                db,
                business_series_id
            )
        )

        if not business_series:
            raise HTTPException(
                status_code=404,
                detail=(
                    "Serie de negocio "
                    "no encontrada"
                )
            )

        BusinessSeriesRepository.delete(
            db=db,
            business_series=(
                business_series
            )
        )