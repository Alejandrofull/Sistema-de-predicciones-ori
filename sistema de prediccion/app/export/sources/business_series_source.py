from typing import Any

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.business_series import BusinessSeries
from app.repositories.business_series_repository import BusinessSeriesRepository
from app.security.permissions import Permissions

from .base_source import ExportSource
from .registry import register_source


class BusinessSeriesExportSource(ExportSource):
    key = "business_series"
    label = "Series de negocio"
    required_permission = Permissions.BUSINESS_SERIES_VIEW

    def get_filters_schema(self, db: Session, current_user: Any) -> list[dict[str, Any]]:
        entity_types = (
            db.execute(
                select(BusinessSeries.entity_type)
                .distinct()
                .order_by(BusinessSeries.entity_type)
            )
            .scalars()
            .all()
        )

        return [
            {
                "name": "entity_type",
                "label": "Tipo de entidad",
                "type": "select",
                "options": [{"value": et, "label": et} for et in entity_types],
            },
            {
                "name": "include_inactive",
                "label": "Incluir inactivas",
                "type": "boolean",
                "default": False,
            },
        ]

    def fetch(self, db: Session, current_user: Any, filters: dict[str, Any]) -> pd.DataFrame:
        entity_type = (filters.get("entity_type") or "").strip().lower() or None
        include_inactive = bool(filters.get("include_inactive", False))

        if entity_type:
            series = BusinessSeriesRepository.get_by_entity_type(
                db=db,
                entity_type=entity_type,
                include_inactive=include_inactive,
            )
        else:
            series = BusinessSeriesRepository.get_all(
                db=db,
                include_inactive=include_inactive,
            )

        return pd.DataFrame(
            [
                {
                    "id": s.id,
                    "external_entity_id": s.external_entity_id,
                    "entity_type": s.entity_type,
                    "nombre": s.name,
                    "activa": s.is_active,
                    "creada": s.created_at,
                }
                for s in series
            ]
        )


register_source(BusinessSeriesExportSource())