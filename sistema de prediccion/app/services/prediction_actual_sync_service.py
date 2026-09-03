from __future__ import annotations

import math

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.prediction import (
    Prediction,
    PredictionResult,
)

from app.services.post_actual_automation_service import (
    PostActualAutomationService,
)


class PredictionActualSyncService:

    # ==========================================
    # SINCRONIZAR UNA OBSERVACIÓN
    # ==========================================

    @staticmethod
    def sync_actual_value(
        db: Session,
        business_series_id: int,
        prediction_date: date,
        actual_value: float,
        run_automation: bool = True
    ) -> dict:

        numeric_actual_value = float(
            actual_value
        )

        if not math.isfinite(
            numeric_actual_value
        ):

            raise ValueError(
                "actual_value debe ser "
                "un número finito"
            )

        if numeric_actual_value < 0:

            raise ValueError(
                "actual_value no puede "
                "ser negativo"
            )

        prediction_result = (
            PredictionActualSyncService
            ._find_latest_prediction_result(
                db=db,
                business_series_id=(
                    business_series_id
                ),
                prediction_date=(
                    prediction_date
                )
            )
        )

        # ==========================================
        # NO EXISTE PREDICCIÓN PARA LA FECHA
        # ==========================================

        if prediction_result is None:

            return {
                "matched": False,
                "updated": False,
                "prediction_result_id": None,
                "prediction_id": None,
                "previous_actual_value": None,
                "actual_value": (
                    numeric_actual_value
                ),
                "automation_executed": False,
                "automation": None,
            }

        # ==========================================
        # OBTENER PREDICCIÓN CABECERA
        # ==========================================

        prediction = db.get(
            Prediction,
            prediction_result.prediction_id
        )

        if prediction is None:

            return {
                "matched": True,
                "updated": False,
                "prediction_result_id": (
                    prediction_result.id
                ),
                "prediction_id": (
                    prediction_result
                    .prediction_id
                ),
                "previous_actual_value": (
                    prediction_result
                    .actual_value
                ),
                "actual_value": (
                    numeric_actual_value
                ),
                "automation_executed": False,
                "automation": {
                    "processed": False,
                    "error": (
                        "No se encontró la "
                        "cabecera Prediction."
                    )
                },
            }

        previous_actual_value = (
            prediction_result.actual_value
        )

        # ==========================================
        # SI EL VALOR YA ES EL MISMO
        # NO VOLVEMOS A EJECUTAR TODO EL CICLO
        # ==========================================

        if (
            previous_actual_value
            is not None
            and math.isclose(
                float(
                    previous_actual_value
                ),
                numeric_actual_value,
                rel_tol=1e-9,
                abs_tol=1e-9
            )
        ):

            return {
                "matched": True,
                "updated": False,
                "prediction_result_id": (
                    prediction_result.id
                ),
                "prediction_id": (
                    prediction_result
                    .prediction_id
                ),
                "previous_actual_value": float(
                    previous_actual_value
                ),
                "actual_value": float(
                    previous_actual_value
                ),
                "automation_executed": False,
                "automation": None,
            }

        # ==========================================
        # ACTUALIZAR VALOR REAL
        # ==========================================

        prediction_result.actual_value = (
            numeric_actual_value
        )

        db.commit()

        db.refresh(
            prediction_result
        )

        # ==========================================
        # AUTOMATIZACIÓN POST-REAL
        # ==========================================

        automation_result = None

        automation_executed = False

        if run_automation:

            try:

                automation_result = (
                    PostActualAutomationService()
                    .process(
                        db=db,
                        prediction=(
                            prediction
                        ),
                        prediction_result=(
                            prediction_result
                        )
                    )
                )

                automation_executed = True

            except Exception as error:

                # IMPORTANTE:
                # actual_value ya fue guardado.
                # Un problema secundario de
                # monitoring/anomalías/retraining
                # no debe eliminar ese valor real.

                try:
                    db.rollback()

                except Exception:
                    pass

                automation_result = {
                    "processed": False,
                    "error": str(
                        error
                    )
                }

        return {
            "matched": True,
            "updated": True,
            "prediction_result_id": (
                prediction_result.id
            ),
            "prediction_id": (
                prediction_result
                .prediction_id
            ),
            "previous_actual_value": (
                float(
                    previous_actual_value
                )
                if previous_actual_value
                is not None
                else None
            ),
            "actual_value": float(
                prediction_result.actual_value
            ),
            "automation_executed": (
                automation_executed
            ),
            "automation": (
                automation_result
            ),
        }

    # ==========================================
    # SINCRONIZAR VARIAS OBSERVACIONES
    # ==========================================

    @staticmethod
    def sync_many(
        db: Session,
        observations: list,
        run_automation: bool = True
    ) -> dict:

        matched = 0
        updated = 0
        unmatched = 0

        automations_executed = 0
        automation_failures = 0

        results = []

        for observation in observations:

            result = (
                PredictionActualSyncService
                .sync_actual_value(
                    db=db,
                    business_series_id=(
                        observation
                        .business_series_id
                    ),
                    prediction_date=(
                        observation
                        .observation_date
                    ),
                    actual_value=float(
                        observation
                        .actual_demand
                    ),
                    run_automation=(
                        run_automation
                    )
                )
            )

            if result[
                "matched"
            ]:

                matched += 1

            else:

                unmatched += 1

            if result[
                "updated"
            ]:

                updated += 1

            if result[
                "automation_executed"
            ]:

                automations_executed += 1

            automation = (
                result.get(
                    "automation"
                )
            )

            if (
                automation
                and automation.get(
                    "processed"
                )
                is False
            ):

                automation_failures += 1

            results.append(
                {
                    "inventory_observation_id": (
                        observation.id
                    ),
                    "business_series_id": (
                        observation
                        .business_series_id
                    ),
                    "observation_date": (
                        observation
                        .observation_date
                    ),
                    **result
                }
            )

        return {
            "total": (
                len(
                    observations
                )
            ),
            "matched": (
                matched
            ),
            "updated": (
                updated
            ),
            "unmatched": (
                unmatched
            ),
            "automations_executed": (
                automations_executed
            ),
            "automation_failures": (
                automation_failures
            ),
            "results": (
                results
            )
        }

    # ==========================================
    # BUSCAR RESULTADO MÁS RECIENTE
    # ==========================================

    @staticmethod
    def _find_latest_prediction_result(
        db: Session,
        business_series_id: int,
        prediction_date: date
    ) -> PredictionResult | None:

        statement = (
            select(
                PredictionResult
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
                Prediction.id.desc(),
                PredictionResult.id.desc()
            )
            .limit(1)
        )

        return db.scalar(
            statement
        )