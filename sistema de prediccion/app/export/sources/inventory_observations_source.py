from typing import Any

import pandas as pd
from sqlalchemy.orm import Session

from app.repositories.business_series_repository import BusinessSeriesRepository
from app.repositories.inventory_observation_repository import (
    InventoryObservationRepository,
)
from app.security.permissions import Permissions

from .base_source import ExportSource, parse_date_filter
from .registry import register_source


class InventoryObservationsExportSource(ExportSource):
    key = "inventory_observations"
    label = "Observaciones de inventario"
    required_permission = Permissions.INVENTORY_VIEW

    def get_filters_schema(self, db: Session, current_user: Any) -> list[dict[str, Any]]:
        series = BusinessSeriesRepository.get_all(db=db, include_inactive=False)
        return [
            {
                "name": "business_series_id",
                "label": "Serie de negocio",
                "type": "select",
                "options": [
                    {"value": str(s.id), "label": s.name or s.external_entity_id}
                    for s in series
                ],
            },
            {
                "name": "phase",
                "label": "Fase",
                "type": "select",
                "options": [
                    {"value": "pre", "label": "Pre (antes de ML)"},
                    {"value": "post", "label": "Post (después de ML)"},
                ],
            },
            {"name": "start_date", "label": "Desde", "type": "date"},
            {"name": "end_date", "label": "Hasta", "type": "date"},
        ]

    def fetch(self, db: Session, current_user: Any, filters: dict[str, Any]) -> pd.DataFrame:
        business_series_id = filters.get("business_series_id")

        observations = InventoryObservationRepository.get_all(
            db=db,
            phase=filters.get("phase") or None,
            business_series_id=int(business_series_id) if business_series_id else None,
            start_date=parse_date_filter(filters.get("start_date")),
            end_date=parse_date_filter(filters.get("end_date")),
            limit=5000,
        )

        return pd.DataFrame(
            [
                {
                    "id": o.id,
                    "business_series_id": o.business_series_id,
                    "fecha": o.observation_date,
                    "fase": o.phase,
                    "stock_inicial": o.opening_stock,
                    "reposicion": o.replenishment_quantity,
                    "demanda_real": o.actual_demand,
                    "stock_final": o.closing_stock,
                    "demanda_pronosticada": o.predicted_demand,
                    "origen": o.source_type,
                }
                for o in observations
            ]
        )


register_source(InventoryObservationsExportSource())
