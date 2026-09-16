from typing import Any

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.prediction import Prediction, PredictionResult
from app.repositories.business_series_repository import BusinessSeriesRepository
from app.security.permissions import Permissions

from .base_source import ExportSource, parse_date_filter
from .registry import register_source


class PredictionsExportSource(ExportSource):
    key = "predictions"
    label = "Predicciones"
    required_permission = Permissions.PREDICTIONS_VIEW

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
            {"name": "start_date", "label": "Desde", "type": "date"},
            {"name": "end_date", "label": "Hasta", "type": "date"},
            {
                "name": "only_with_actual",
                "label": "Solo con valor real registrado",
                "type": "boolean",
                "default": False,
            },
        ]

    def fetch(self, db: Session, current_user: Any, filters: dict[str, Any]) -> pd.DataFrame:
        query = select(PredictionResult, Prediction).join(
            Prediction, Prediction.id == PredictionResult.prediction_id
        )

        business_series_id = filters.get("business_series_id")
        if business_series_id:
            query = query.where(Prediction.business_series_id == int(business_series_id))

        start_date = parse_date_filter(filters.get("start_date"))
        if start_date:
            query = query.where(PredictionResult.prediction_date >= start_date)

        end_date = parse_date_filter(filters.get("end_date"))
        if end_date:
            query = query.where(PredictionResult.prediction_date <= end_date)

        if filters.get("only_with_actual"):
            query = query.where(PredictionResult.actual_value.is_not(None))

        query = query.order_by(PredictionResult.prediction_date.asc())

        rows = db.execute(query).all()

        return pd.DataFrame(
            [
                {
                    "prediction_id": prediction.id,
                    "business_series_id": prediction.business_series_id,
                    "model_id": prediction.model_id,
                    "fecha": result.prediction_date,
                    "valor_predicho": result.predicted_value,
                    "valor_real": result.actual_value,
                    "limite_inferior": result.lower_bound,
                    "limite_superior": result.upper_bound,
                }
                for result, prediction in rows
            ]
        )


register_source(PredictionsExportSource())
