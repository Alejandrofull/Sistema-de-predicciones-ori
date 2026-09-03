from __future__ import annotations

from datetime import date

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories.business_series_repository import (
    BusinessSeriesRepository,
)

from app.repositories.inventory_observation_repository import (
    InventoryObservationRepository,
)

from app.services.prediction_actual_sync_service import (
    PredictionActualSyncService,
)


class InventoryKPIService:

    # ==========================================
    # CREAR OBSERVACIÓN
    # ==========================================

    @staticmethod
    def create_observation(
        db: Session,
        user_id: int,
        business_series_id: int,
        observation_date: date,
        phase: str,
        opening_stock: float,
        replenishment_quantity: float,
        actual_demand: float,
        closing_stock: float,
        predicted_demand: float | None,
        source_type: str
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
            InventoryObservationRepository
            .get_existing(
                db=db,
                business_series_id=(
                    business_series_id
                ),
                observation_date=(
                    observation_date
                ),
                phase=phase
            )
        )

        if existing:

            raise HTTPException(
                status_code=409,
                detail=(
                    "Ya existe una observación "
                    "para esta serie, fecha "
                    "y fase"
                )
            )

        observation = (
            InventoryObservationRepository
            .create(
                db=db,
                user_id=user_id,
                business_series_id=(
                    business_series_id
                ),
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

        # ==========================================
        # SINCRONIZAR VALOR REAL
        # SOLO EN FASE POST
        # ==========================================

        sync_result = None

        if phase == "post":

            try:

                sync_result = (
                    PredictionActualSyncService
                    .sync_actual_value(
                        db=db,
                        business_series_id=(
                            business_series_id
                        ),
                        prediction_date=(
                            observation_date
                        ),
                        actual_value=(
                            actual_demand
                        )
                    )
                )

            except Exception:

                try:
                    db.rollback()

                except Exception:
                    pass

                sync_result = {
                    "matched": False,
                    "updated": False
                }

        observation._prediction_sync = (
            sync_result
        )

        return observation

    # ==========================================
    # BULK
    # ==========================================

    def create_many(
        self,
        db: Session,
        user_id: int,
        observations: list
    ) -> list:

        created = []

        for item in observations:

            observation = (
                self.create_observation(
                    db=db,
                    user_id=user_id,
                    business_series_id=(
                        item.business_series_id
                    ),
                    observation_date=(
                        item.observation_date
                    ),
                    phase=item.phase,
                    opening_stock=(
                        item.opening_stock
                    ),
                    replenishment_quantity=(
                        item.replenishment_quantity
                    ),
                    actual_demand=(
                        item.actual_demand
                    ),
                    closing_stock=float(
                        item.closing_stock
                    ),
                    predicted_demand=(
                        item.predicted_demand
                    ),
                    source_type=(
                        item.source_type
                    )
                )
            )

            created.append(
                observation
            )

        return created

    # ==========================================
    # COMPARACIÓN PRE VS POST
    # ==========================================

    def compare(
        self,
        db: Session,
        business_series_id: int | None = None,
        start_date: date | None = None,
        end_date: date | None = None
    ) -> dict:

        if business_series_id is not None:

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

        pre_observations = (
            InventoryObservationRepository
            .get_all(
                db=db,
                phase="pre",
                business_series_id=(
                    business_series_id
                ),
                start_date=start_date,
                end_date=end_date,
                limit=100000
            )
        )

        post_observations = (
            InventoryObservationRepository
            .get_all(
                db=db,
                phase="post",
                business_series_id=(
                    business_series_id
                ),
                start_date=start_date,
                end_date=end_date,
                limit=100000
            )
        )

        pre = (
            self._calculate_phase_kpis(
                phase="pre",
                observations=(
                    pre_observations
                )
            )
        )

        post = (
            self._calculate_phase_kpis(
                phase="post",
                observations=(
                    post_observations
                )
            )
        )

        improvement = {
            "stockout_units_reduction_percent": (
                self._reduction_percent(
                    pre[
                        "total_stockout_units"
                    ],
                    post[
                        "total_stockout_units"
                    ]
                )
            ),
            "stockout_events_reduction_percent": (
                self._reduction_percent(
                    float(
                        pre[
                            "stockout_events"
                        ]
                    ),
                    float(
                        post[
                            "stockout_events"
                        ]
                    )
                )
            ),
            "overstock_reduction_percent": (
                self._reduction_percent(
                    pre[
                        "total_overstock_units"
                    ],
                    post[
                        "total_overstock_units"
                    ]
                )
            ),
            "service_level_improvement_points": (
                self._difference(
                    post[
                        "service_level_percent"
                    ],
                    pre[
                        "service_level_percent"
                    ]
                )
            ),
            "forecast_mae_improvement_percent": (
                self._improvement_optional(
                    pre[
                        "forecast_mae"
                    ],
                    post[
                        "forecast_mae"
                    ]
                )
            ),
            "forecast_mape_improvement_percent": (
                self._improvement_optional(
                    pre[
                        "forecast_mape"
                    ],
                    post[
                        "forecast_mape"
                    ]
                )
            )
        }

        return {
            "business_series_id": (
                business_series_id
            ),
            "pre": (
                pre
            ),
            "post": (
                post
            ),
            "improvement": (
                improvement
            )
        }

    # ==========================================
    # CALCULAR KPIS DE UNA FASE
    # ==========================================

    @staticmethod
    def _calculate_phase_kpis(
        phase: str,
        observations: list
    ) -> dict:

        if not observations:

            return {
                "phase": phase,
                "observations": 0,
                "total_demand": 0.0,
                "total_available_stock": 0.0,
                "total_served_demand": 0.0,
                "total_stockout_units": 0.0,
                "total_overstock_units": 0.0,
                "stockout_events": 0,
                "stockout_rate_percent": 0.0,
                "service_level_percent": 0.0,
                "average_closing_stock": 0.0,
                "average_stockout_units": 0.0,
                "average_overstock_units": 0.0,
                "forecast_mae": None,
                "forecast_mape": None
            }

        total_demand = 0.0
        total_available = 0.0
        total_served = 0.0

        total_stockout = 0.0
        total_overstock = 0.0

        total_closing_stock = 0.0

        stockout_events = 0

        forecast_absolute_errors = []
        forecast_percentage_errors = []

        for observation in observations:

            available = (
                float(
                    observation.opening_stock
                )
                +
                float(
                    observation
                    .replenishment_quantity
                )
            )

            demand = float(
                observation.actual_demand
            )

            served = min(
                available,
                demand
            )

            stockout_units = max(
                demand - available,
                0.0
            )

            overstock_units = max(
                available - demand,
                0.0
            )

            total_demand += demand
            total_available += available
            total_served += served

            total_stockout += (
                stockout_units
            )

            total_overstock += (
                overstock_units
            )

            total_closing_stock += float(
                observation.closing_stock
            )

            if stockout_units > 0:

                stockout_events += 1

            predicted = (
                observation.predicted_demand
            )

            if predicted is not None:

                error = abs(
                    demand
                    -
                    float(
                        predicted
                    )
                )

                forecast_absolute_errors.append(
                    error
                )

                if demand != 0:

                    forecast_percentage_errors.append(
                        (
                            error
                            /
                            abs(
                                demand
                            )
                        )
                        *
                        100.0
                    )

        count = len(
            observations
        )

        stockout_rate = (
            stockout_events
            /
            count
            *
            100.0
        )

        if total_demand > 0:

            service_level = (
                total_served
                /
                total_demand
                *
                100.0
            )

        else:

            service_level = 100.0

        forecast_mae = (
            sum(
                forecast_absolute_errors
            )
            /
            len(
                forecast_absolute_errors
            )
            if forecast_absolute_errors
            else None
        )

        forecast_mape = (
            sum(
                forecast_percentage_errors
            )
            /
            len(
                forecast_percentage_errors
            )
            if forecast_percentage_errors
            else None
        )

        return {
            "phase": phase,
            "observations": count,
            "total_demand": float(
                total_demand
            ),
            "total_available_stock": float(
                total_available
            ),
            "total_served_demand": float(
                total_served
            ),
            "total_stockout_units": float(
                total_stockout
            ),
            "total_overstock_units": float(
                total_overstock
            ),
            "stockout_events": (
                stockout_events
            ),
            "stockout_rate_percent": float(
                stockout_rate
            ),
            "service_level_percent": float(
                service_level
            ),
            "average_closing_stock": float(
                total_closing_stock
                /
                count
            ),
            "average_stockout_units": float(
                total_stockout
                /
                count
            ),
            "average_overstock_units": float(
                total_overstock
                /
                count
            ),
            "forecast_mae": (
                float(
                    forecast_mae
                )
                if forecast_mae
                is not None
                else None
            ),
            "forecast_mape": (
                float(
                    forecast_mape
                )
                if forecast_mape
                is not None
                else None
            )
        }

    # ==========================================
    # REDUCCIÓN %
    # ==========================================

    @staticmethod
    def _reduction_percent(
        before: float,
        after: float
    ) -> float | None:

        if before == 0:

            if after == 0:
                return 0.0

            return None

        return float(
            (
                before
                -
                after
            )
            /
            before
            *
            100.0
        )

    # ==========================================
    # DIFERENCIA
    # ==========================================

    @staticmethod
    def _difference(
        after: float,
        before: float
    ) -> float:

        return float(
            after
            -
            before
        )

    # ==========================================
    # MEJORA DE ERROR
    # ==========================================

    @staticmethod
    def _improvement_optional(
        before: float | None,
        after: float | None
    ) -> float | None:

        if (
            before is None
            or after is None
        ):

            return None

        if before == 0:

            if after == 0:
                return 0.0

            return None

        return float(
            (
                before
                -
                after
            )
            /
            before
            *
            100.0
        )