from __future__ import annotations

from datetime import date

import pandas as pd

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.prediction import (
    Prediction,
    PredictionResult,
)

from app.repositories.business_series_repository import (
    BusinessSeriesRepository,
)

from app.repositories.inventory_observation_repository import (
    InventoryObservationRepository,
)

from app.services.audit_service import (
    AuditService,
)

from app.services.prediction_actual_sync_service import (
    PredictionActualSyncService,
)


class InventoryImportService:

    # ==========================================
    # IMPORTAR DATAFRAME
    # ==========================================

    def import_dataframe(
        self,
        db: Session,
        dataframe: pd.DataFrame,
        filename: str,
        user_id: int,
        phase: str,
        business_series_id: int | None,
        date_column: str,
        entity_column: str | None,
        opening_stock_column: str,
        replenishment_column: str,
        actual_demand_column: str,
        closing_stock_column: str | None,
        predicted_demand_column: str | None,
        source_type: str,
        auto_match_prediction: bool,
        sync_actual_values: bool = True
    ) -> dict:

        phase = (
            phase
            .strip()
            .lower()
        )

        if phase not in {
            "pre",
            "post",
        }:

            raise HTTPException(
                status_code=400,
                detail=(
                    "phase debe ser "
                    "'pre' o 'post'"
                )
            )

        if dataframe.empty:

            raise HTTPException(
                status_code=400,
                detail=(
                    "El archivo no contiene "
                    "registros"
                )
            )

        dataframe = dataframe.copy()

        dataframe.columns = [
            str(
                column
            ).strip()
            for column
            in dataframe.columns
        ]

        required_columns = [
            date_column,
            opening_stock_column,
            actual_demand_column,
        ]

        if (
            business_series_id is None
            and entity_column
        ):

            required_columns.append(
                entity_column
            )

        missing_columns = [
            column
            for column
            in required_columns
            if column
            not in dataframe.columns
        ]

        if missing_columns:

            raise HTTPException(
                status_code=400,
                detail={
                    "message": (
                        "Faltan columnas "
                        "obligatorias"
                    ),
                    "missing_columns": (
                        missing_columns
                    )
                }
            )

        # ==========================================
        # SERIE FIJA
        # ==========================================

        fixed_business_series = None

        if business_series_id is not None:

            fixed_business_series = (
                BusinessSeriesRepository
                .get_by_id(
                    db,
                    business_series_id
                )
            )

            if not fixed_business_series:

                raise HTTPException(
                    status_code=404,
                    detail=(
                        "Serie de negocio "
                        "no encontrada"
                    )
                )

        # ==========================================
        # CONTADORES
        # ==========================================

        imported_rows = 0
        skipped_rows = 0

        matched_predictions = 0

        actual_values_synced = 0
        actual_values_unmatched = 0

        calculated_closing_stock = 0

        errors = []

        created_ids = []

        # ==========================================
        # RECORRER FILAS
        # ==========================================

        for index, row in (
            dataframe.iterrows()
        ):

            row_number = int(
                index
            ) + 2

            raw_data = (
                self._serialize_row(
                    row
                )
            )

            try:

                # ==================================
                # FECHA
                # ==================================

                observation_date = (
                    self._parse_date(
                        row.get(
                            date_column
                        )
                    )
                )

                # ==================================
                # BUSINESS SERIES
                # ==================================

                if fixed_business_series:

                    business_series = (
                        fixed_business_series
                    )

                else:

                    business_series = (
                        self._resolve_business_series(
                            db=db,
                            entity_value=(
                                row.get(
                                    entity_column
                                )
                            )
                        )
                    )

                # ==================================
                # DUPLICADOS
                # ==================================

                existing = (
                    InventoryObservationRepository
                    .get_existing(
                        db=db,
                        business_series_id=(
                            business_series.id
                        ),
                        observation_date=(
                            observation_date
                        ),
                        phase=phase
                    )
                )

                if existing:

                    skipped_rows += 1

                    errors.append(
                        {
                            "row_number": (
                                row_number
                            ),
                            "message": (
                                "Ya existe una "
                                "observación para "
                                "esa serie, fecha "
                                "y fase"
                            ),
                            "raw_data": (
                                raw_data
                            )
                        }
                    )

                    continue

                # ==================================
                # STOCK INICIAL
                # ==================================

                opening_stock = (
                    self._parse_non_negative_float(
                        row.get(
                            opening_stock_column
                        ),
                        opening_stock_column
                    )
                )

                # ==================================
                # REPOSICIÓN
                # ==================================

                if (
                    replenishment_column
                    in dataframe.columns
                ):

                    replenishment_quantity = (
                        self._parse_non_negative_float(
                            row.get(
                                replenishment_column
                            ),
                            replenishment_column,
                            default=0.0
                        )
                    )

                else:

                    replenishment_quantity = 0.0

                # ==================================
                # DEMANDA REAL
                # ==================================

                actual_demand = (
                    self._parse_non_negative_float(
                        row.get(
                            actual_demand_column
                        ),
                        actual_demand_column
                    )
                )

                # ==================================
                # STOCK FINAL
                # ==================================

                closing_stock = None

                if (
                    closing_stock_column
                    and closing_stock_column
                    in dataframe.columns
                ):

                    closing_value = (
                        row.get(
                            closing_stock_column
                        )
                    )

                    if not self._is_missing(
                        closing_value
                    ):

                        closing_stock = (
                            self._parse_non_negative_float(
                                closing_value,
                                closing_stock_column
                            )
                        )

                if closing_stock is None:

                    available = (
                        opening_stock
                        +
                        replenishment_quantity
                    )

                    closing_stock = max(
                        0.0,
                        available
                        -
                        actual_demand
                    )

                    calculated_closing_stock += 1

                # ==================================
                # PRONÓSTICO DEL ARCHIVO
                # ==================================

                predicted_demand = None

                if (
                    predicted_demand_column
                    and predicted_demand_column
                    in dataframe.columns
                ):

                    raw_prediction = (
                        row.get(
                            predicted_demand_column
                        )
                    )

                    if not self._is_missing(
                        raw_prediction
                    ):

                        predicted_demand = (
                            self._parse_non_negative_float(
                                raw_prediction,
                                predicted_demand_column
                            )
                        )

                # ==================================
                # PRONÓSTICO DEL SISTEMA
                # ==================================

                if (
                    predicted_demand is None
                    and auto_match_prediction
                ):

                    matched_prediction = (
                        self._find_prediction_value(
                            db=db,
                            business_series_id=(
                                business_series.id
                            ),
                            prediction_date=(
                                observation_date
                            )
                        )
                    )

                    if matched_prediction is not None:

                        predicted_demand = (
                            matched_prediction
                        )

                        matched_predictions += 1

                # ==================================
                # CREAR OBSERVACIÓN
                # ==================================

                observation = (
                    InventoryObservationRepository
                    .create(
                        db=db,
                        business_series_id=(
                            business_series.id
                        ),
                        user_id=user_id,
                        observation_date=(
                            observation_date
                        ),
                        phase=phase,
                        opening_stock=(
                            opening_stock
                        ),
                        replenishment_quantity=(
                            replenishment_quantity
                        ),
                        actual_demand=(
                            actual_demand
                        ),
                        closing_stock=(
                            closing_stock
                        ),
                        predicted_demand=(
                            predicted_demand
                        ),
                        source_type=(
                            source_type
                        )
                    )
                )

                created_ids.append(
                    observation.id
                )

                imported_rows += 1

                # ==================================
                # SINCRONIZAR ACTUAL_VALUE
                # ==================================

                if (
                    phase == "post"
                    and sync_actual_values
                ):

                    sync_result = (
                        PredictionActualSyncService
                        .sync_actual_value(
                            db=db,
                            business_series_id=(
                                business_series.id
                            ),
                            prediction_date=(
                                observation_date
                            ),
                            actual_value=(
                                actual_demand
                            )
                        )
                    )

                    if sync_result[
                        "matched"
                    ]:

                        actual_values_synced += 1

                    else:

                        actual_values_unmatched += 1

            except Exception as error:

                try:

                    db.rollback()

                except Exception:
                    pass

                skipped_rows += 1

                errors.append(
                    {
                        "row_number": (
                            row_number
                        ),
                        "message": str(
                            error
                        ),
                        "raw_data": (
                            raw_data
                        )
                    }
                )

        # ==========================================
        # AUDITORÍA
        # ==========================================

        AuditService.log_safe(
            db=db,
            user_id=user_id,
            action=(
                "inventory.import"
            ),
            entity=(
                "inventory_observation"
            ),
            entity_id=None,
            details={
                "filename": filename,
                "phase": phase,
                "total_rows": int(
                    len(
                        dataframe
                    )
                ),
                "imported_rows": (
                    imported_rows
                ),
                "skipped_rows": (
                    skipped_rows
                ),
                "matched_predictions": (
                    matched_predictions
                ),
                "actual_values_synced": (
                    actual_values_synced
                ),
                "actual_values_unmatched": (
                    actual_values_unmatched
                ),
                "business_series_id": (
                    business_series_id
                )
            }
        )

        return {
            "filename": (
                filename
            ),
            "phase": (
                phase
            ),
            "total_rows": int(
                len(
                    dataframe
                )
            ),
            "imported_rows": (
                imported_rows
            ),
            "skipped_rows": (
                skipped_rows
            ),
            "matched_predictions": (
                matched_predictions
            ),
            "actual_values_synced": (
                actual_values_synced
            ),
            "actual_values_unmatched": (
                actual_values_unmatched
            ),
            "calculated_closing_stock": (
                calculated_closing_stock
            ),
            "errors": (
                errors
            ),
            "created_observation_ids": (
                created_ids
            )
        }

    # ==========================================
    # BUSINESS SERIES
    # ==========================================

    @staticmethod
    def _resolve_business_series(
        db: Session,
        entity_value
    ):

        if (
            entity_value is None
            or pd.isna(
                entity_value
            )
        ):

            raise ValueError(
                "No se encontró el producto "
                "o serie de negocio"
            )

        raw_value = (
            str(
                entity_value
            )
            .strip()
        )

        if not raw_value:

            raise ValueError(
                "El producto o serie "
                "está vacío"
            )

        candidates = [
            raw_value,
            f"product:{raw_value}",
        ]

        for candidate in candidates:

            series = (
                BusinessSeriesRepository
                .get_by_external_entity_id(
                    db=db,
                    external_entity_id=(
                        candidate
                    ),
                    entity_type=None
                )
            )

            if series:

                return series

        all_series = (
            BusinessSeriesRepository
            .get_all(
                db=db,
                include_inactive=True
            )
        )

        normalized_value = (
            raw_value.lower()
        )

        for series in all_series:

            if (
                series.name
                and series.name
                .strip()
                .lower()
                == normalized_value
            ):

                return series

        raise ValueError(
            "No se encontró una "
            "BusinessSeries para "
            f"'{raw_value}'"
        )

    # ==========================================
    # BUSCAR PREDICCIÓN
    # ==========================================

    @staticmethod
    def _find_prediction_value(
        db: Session,
        business_series_id: int,
        prediction_date: date
    ) -> float | None:

        statement = (
            select(
                PredictionResult.predicted_value
            )
            .join(
                Prediction,
                Prediction.id
                == PredictionResult.prediction_id
            )
            .where(
                Prediction.business_series_id
                == business_series_id,
                PredictionResult.prediction_date
                == prediction_date,
                Prediction.status
                == "completed"
            )
            .order_by(
                Prediction.created_at.desc(),
                Prediction.id.desc()
            )
            .limit(1)
        )

        value = db.scalar(
            statement
        )

        if value is None:

            return None

        return float(
            value
        )

    # ==========================================
    # FECHA
    # ==========================================

    @staticmethod
    def _parse_date(
        value
    ) -> date:

        if (
            value is None
            or pd.isna(
                value
            )
        ):

            raise ValueError(
                "La fecha es obligatoria"
            )

        parsed = pd.to_datetime(
            value,
            errors="coerce"
        )

        if pd.isna(
            parsed
        ):

            raise ValueError(
                f"Fecha inválida: {value}"
            )

        return parsed.date()

    # ==========================================
    # NÚMERO
    # ==========================================

    @staticmethod
    def _parse_non_negative_float(
        value,
        field_name: str,
        default: float | None = None
    ) -> float:

        if (
            value is None
            or InventoryImportService
            ._is_missing(
                value
            )
        ):

            if default is not None:

                return float(
                    default
                )

            raise ValueError(
                f"'{field_name}' "
                "es obligatorio"
            )

        try:

            result = float(
                value
            )

        except (
            TypeError,
            ValueError,
        ):

            raise ValueError(
                f"'{field_name}' "
                "debe ser numérico"
            )

        if result < 0:

            raise ValueError(
                f"'{field_name}' "
                "no puede ser negativo"
            )

        return result

    # ==========================================
    # MISSING
    # ==========================================

    @staticmethod
    def _is_missing(
        value
    ) -> bool:

        try:

            return bool(
                pd.isna(
                    value
                )
            )

        except Exception:

            return False

    # ==========================================
    # SERIALIZAR FILA
    # ==========================================

    @staticmethod
    def _serialize_row(
        row
    ) -> dict:

        result = {}

        for key, value in (
            row.to_dict().items()
        ):

            if (
                value is None
                or InventoryImportService
                ._is_missing(
                    value
                )
            ):

                result[
                    str(
                        key
                    )
                ] = None

            elif hasattr(
                value,
                "isoformat"
            ):

                result[
                    str(
                        key
                    )
                ] = (
                    value.isoformat()
                )

            else:

                result[
                    str(
                        key
                    )
                ] = value

        return result