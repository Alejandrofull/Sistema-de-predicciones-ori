from __future__ import annotations

from fastapi import (
    HTTPException,
)

from sqlalchemy.orm import Session

from app.repositories.anomaly_repository import (
    AnomalyRepository,
)

from app.repositories.business_series_repository import (
    BusinessSeriesRepository,
)

from app.repositories.dataset_repository import (
    DatasetRepository,
)

from app.repositories.model_evaluation_repository import (
    ModelEvaluationRepository,
)

from app.repositories.model_repository import (
    ModelRepository,
)

from app.repositories.model_version_repository import (
    ModelVersionRepository,
)

from app.repositories.prediction_repository import (
    PredictionRepository,
)

from app.services.inventory_kpi_service import (
    InventoryKPIService,
)

from app.services.inventory_statistics_service import (
    InventoryStatisticsService,
)

from app.services.performance_monitoring_service import (
    PerformanceMonitoringService,
)


class ThesisReportService:

    DEFAULT_STATISTICAL_INDICATORS = [
        "stockout_units",
        "overstock_units",
        "service_level",
        "closing_stock",
        "forecast_absolute_error",
        "forecast_ape",
    ]

    PERFORMANCE_LIMIT = 200

    PERFORMANCE_MINIMUM_OBSERVATIONS = 5

    # 0.20 = degradación relativa del 20 %
    RMSE_DEGRADATION_THRESHOLD = 0.20

    MAPE_THRESHOLD = 20.0

    def __init__(self):

        self.inventory_service = (
            InventoryKPIService()
        )

        self.statistics_service = (
            InventoryStatisticsService()
        )

        self.performance_service = (
            PerformanceMonitoringService()
        )

    # ==========================================
    # CONSTRUIR REPORTE
    # ==========================================

    def build_context(
        self,
        db: Session,
        business_series_id: int,
        include_predictions: bool = True,
        include_inventory: bool = True,
        include_statistics: bool = True,
        include_anomalies: bool = True,
        prediction_limit: int = 50,
        anomaly_limit: int = 50,
        alpha: float = 0.05,
        statistical_indicators: list[str] | None = None
    ) -> dict:

        # ======================================
        # 1. SERIE
        # ======================================

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

        # ======================================
        # 2. MODELOS
        # ======================================

        models = (
            ModelRepository
            .get_by_business_series(
                db=db,
                business_series_id=(
                    business_series_id
                )
            )
        )

        models_by_id = {
            model.id: model
            for model in models
        }

        active_model = (
            ModelRepository
            .get_active_by_business_series(
                db=db,
                business_series_id=(
                    business_series_id
                )
            )
        )

        # ======================================
        # 3. EVALUACIONES
        # ======================================

        all_evaluations = []

        for model in models:

            all_evaluations.extend(
                ModelEvaluationRepository
                .get_by_model(
                    db=db,
                    model_id=model.id
                )
            )

        best_evaluation = (
            self._resolve_best_evaluation(
                all_evaluations
            )
        )

        comparison_evaluations = (
            self._resolve_comparison_evaluations(
                db=db,
                best_evaluation=(
                    best_evaluation
                ),
                models=models
            )
        )

        # ======================================
        # 4. DATASET DE LA EVALUACIÓN GANADORA
        # ======================================

        dataset = None

        if (
            best_evaluation
            and best_evaluation.dataset_id
        ):

            dataset = (
                DatasetRepository
                .get_by_id(
                    db,
                    best_evaluation.dataset_id
                )
            )

        # ======================================
        # 5. VERSION ACTIVA
        # ======================================

        active_version = None

        if active_model:

            active_version = (
                ModelVersionRepository
                .get_active_by_model(
                    db=db,
                    model_id=(
                        active_model.id
                    )
                )
            )

        # ======================================
        # 6. MODELOS COMPARADOS
        # ======================================

        model_records = (
            self._build_model_records(
                evaluations=(
                    comparison_evaluations
                ),
                models_by_id=(
                    models_by_id
                )
            )
        )

        # ======================================
        # 7. GANADOR
        # ======================================

        winner_data = (
            self._build_winner_data(
                evaluation=(
                    best_evaluation
                ),
                models_by_id=(
                    models_by_id
                )
            )
        )

        # ======================================
        # 8. ROLLING ORIGIN
        # ======================================

        rolling_origin = (
            self._build_rolling_origin_data(
                best_evaluation
            )
        )

        # ======================================
        # 9. PERFORMANCE REAL
        # ======================================

        performance = (
            self._safe_performance(
                db=db,
                business_series_id=(
                    business_series_id
                ),
                has_active_model=(
                    active_model
                    is not None
                )
            )
        )

        # ======================================
        # 10. PREDICCIONES
        # ======================================

        prediction_records = []

        if include_predictions:

            predictions = (
                PredictionRepository
                .get_by_business_series(
                    db=db,
                    business_series_id=(
                        business_series_id
                    ),
                    limit=prediction_limit
                )
            )

            prediction_records = [
                {
                    "id": prediction.id,
                    "model_id": (
                        prediction.model_id
                    ),
                    "model_version_id": (
                        prediction
                        .model_version_id
                    ),
                    "horizon": (
                        prediction.horizon
                    ),
                    "start_date": (
                        prediction.start_date
                    ),
                    "end_date": (
                        prediction.end_date
                    ),
                    "status": (
                        prediction.status
                    ),
                    "created_at": (
                        prediction.created_at
                    ),
                }
                for prediction
                in predictions
            ]

        # ======================================
        # 11. INVENTARIO
        # ======================================

        inventory = None

        if include_inventory:

            inventory = (
                self.inventory_service.compare(
                    db=db,
                    business_series_id=(
                        business_series_id
                    )
                )
            )

        # ======================================
        # 12. ESTADÍSTICA
        # ======================================

        statistics = None

        if include_statistics:

            indicators = (
                statistical_indicators
                or
                self.DEFAULT_STATISTICAL_INDICATORS
            )

            statistics = (
                self._safe_statistics(
                    db=db,
                    business_series_id=(
                        business_series_id
                    ),
                    indicators=indicators,
                    alpha=alpha
                )
            )

        # ======================================
        # 13. ANOMALÍAS
        # ======================================

        anomaly_records = []

        if include_anomalies:

            anomalies = (
                AnomalyRepository
                .get_all(
                    db=db,
                    business_series_id=(
                        business_series_id
                    ),
                    limit=anomaly_limit
                )
            )

            anomaly_records = [
                {
                    "id": anomaly.id,
                    "type": (
                        anomaly.anomaly_type
                    ),
                    "method": (
                        anomaly.method
                    ),
                    "severity": (
                        anomaly.severity
                    ),
                    "status": (
                        anomaly.status
                    ),
                    "observed_value": (
                        anomaly.observed_value
                    ),
                    "expected_value": (
                        anomaly.expected_value
                    ),
                    "deviation": (
                        anomaly.deviation
                    ),
                    "score": (
                        anomaly.score
                    ),
                    "detected_at": (
                        anomaly.detected_at
                    ),
                }
                for anomaly
                in anomalies
            ]

        # ======================================
        # 14. SECCIONES
        # ======================================

        sections = []

        sections.append(
            {
                "title": (
                    "1. Información general"
                ),
                "type": "key_value",
                "data": {
                    "business_series_id": (
                        business_series.id
                    ),
                    "external_entity_id": (
                        business_series
                        .external_entity_id
                    ),
                    "entity_type": (
                        business_series.entity_type
                    ),
                    "name": (
                        business_series.name
                    ),
                    "is_active": (
                        business_series.is_active
                    ),
                    "dimensions": (
                        business_series.dimensions
                    ),
                }
            }
        )

        sections.append(
            {
                "title": (
                    "2. Dataset utilizado"
                ),
                "type": "key_value",
                "data": (
                    self._dataset_data(
                        dataset
                    )
                )
            }
        )

        sections.append(
            {
                "title": (
                    "3. Modelo activo en producción"
                ),
                "type": "key_value",
                "data": (
                    self._active_model_data(
                        active_model=active_model,
                        active_version=active_version
                    )
                )
            }
        )

        sections.append(
            {
                "title": (
                    "4. Comparación de modelos"
                ),
                "type": "table",
                "records": (
                    model_records
                )
            }
        )

        sections.append(
            {
                "title": (
                    "5. Modelo mejor evaluado"
                ),
                "type": "key_value",
                "data": (
                    winner_data
                )
            }
        )

        sections.append(
            {
                "title": (
                    "6. Rolling-origin backtesting"
                ),
                "type": "key_value",
                "data": (
                    rolling_origin
                )
            }
        )

        sections.append(
            {
                "title": (
                    "7. Desempeño con valores reales"
                ),
                "type": "key_value",
                "data": (
                    self._performance_data(
                        performance
                    )
                )
            }
        )

        if include_predictions:

            sections.append(
                {
                    "title": (
                        "8. Predicciones realizadas"
                    ),
                    "type": "table",
                    "records": (
                        prediction_records
                    )
                }
            )

        if include_inventory:

            sections.extend(
                self._inventory_sections(
                    inventory
                )
            )

        if include_statistics:

            sections.append(
                {
                    "title": (
                        "12. Análisis estadístico "
                        "PRE vs POST"
                    ),
                    "type": "table",
                    "text": (
                        self._statistics_text(
                            statistics
                        )
                    ),
                    "records": (
                        self._statistics_records(
                            statistics
                        )
                    )
                }
            )

        if include_anomalies:

            sections.append(
                {
                    "title": (
                        "13. Anomalías detectadas"
                    ),
                    "type": "table",
                    "records": (
                        anomaly_records
                    )
                }
            )

        sections.append(
            {
                "title": (
                    "14. Interpretación general"
                ),
                "type": "text",
                "text": (
                    self._build_interpretation(
                        inventory=inventory,
                        statistics=statistics,
                        performance=performance
                    )
                )
            }
        )

        # ======================================
        # RESULTADO
        # ======================================

        return {
            "title": (
                "Reporte consolidado de "
                "resultados del sistema "
                "de predicción de demanda"
            ),
            "subtitle": (
                business_series.name
                or
                business_series
                .external_entity_id
            ),
            "description": (
                "Reporte técnico-operacional "
                "que consolida evaluación de "
                "modelos predictivos, "
                "backtesting rolling-origin, "
                "desempeño observado, "
                "indicadores de inventario "
                "y análisis estadístico."
            ),
            "business_series_id": (
                business_series_id
            ),
            "methodological_note": (
                "Las diferencias PRE y POST "
                "presentadas en este reporte "
                "corresponden a cambios observados "
                "en los registros disponibles. "
                "La significancia estadística se "
                "presenta cuando existen datos "
                "suficientes. Estos resultados, "
                "por sí solos, no establecen una "
                "relación causal."
            ),
            "sections": (
                sections
            ),
        }

    # ==========================================
    # MEJOR EVALUACIÓN
    # ==========================================

    @staticmethod
    def _resolve_best_evaluation(
        evaluations: list
    ):

        if not evaluations:

            return None

        best_candidates = [
            evaluation
            for evaluation
            in evaluations
            if evaluation.is_best_model
        ]

        if best_candidates:

            return max(
                best_candidates,
                key=lambda item: (
                    item.evaluated_at
                )
            )

        valid_scores = [
            evaluation
            for evaluation
            in evaluations
            if (
                evaluation.score
                is not None
            )
        ]

        if valid_scores:

            return min(
                valid_scores,
                key=lambda item: (
                    float(
                        item.score
                    )
                )
            )

        valid_rmse = [
            evaluation
            for evaluation
            in evaluations
            if (
                evaluation.rmse
                is not None
            )
        ]

        if valid_rmse:

            return min(
                valid_rmse,
                key=lambda item: (
                    float(
                        item.rmse
                    )
                )
            )

        return max(
            evaluations,
            key=lambda item: (
                item.evaluated_at
            )
        )

    # ==========================================
    # EVALUACIONES DE COMPARACIÓN
    # ==========================================

    @staticmethod
    def _resolve_comparison_evaluations(
        db: Session,
        best_evaluation,
        models: list
    ) -> list:

        if (
            best_evaluation
            and
            best_evaluation.training_id
        ):

            evaluations = (
                ModelEvaluationRepository
                .get_by_training(
                    db=db,
                    training_id=(
                        best_evaluation
                        .training_id
                    )
                )
            )

            if evaluations:

                return evaluations

        evaluations = []

        for model in models:

            evaluation = (
                ModelEvaluationRepository
                .get_latest_by_model(
                    db=db,
                    model_id=model.id
                )
            )

            if evaluation:

                evaluations.append(
                    evaluation
                )

        return evaluations

    # ==========================================
    # MODELOS
    # ==========================================

    @staticmethod
    def _build_model_records(
        evaluations: list,
        models_by_id: dict
    ) -> list[dict]:

        records = []

        for evaluation in evaluations:

            model = (
                models_by_id.get(
                    evaluation.model_id
                )
            )

            config = (
                evaluation.evaluation_config
                or {}
            )

            backtesting = (
                config.get(
                    "backtesting",
                    {}
                )
            )

            mean_metrics = (
                backtesting.get(
                    "mean_metrics",
                    {}
                )
            )

            selection = (
                config.get(
                    "selection",
                    {}
                )
            )

            records.append(
                {
                    "ranking": (
                        evaluation
                        .ranking_position
                    ),
                    "model": (
                        model.model_type
                        if model
                        else evaluation.model_id
                    ),
                    "version": (
                        model.version
                        if model
                        else None
                    ),
                    "holdout_rmse": (
                        evaluation.rmse
                    ),
                    "holdout_mae": (
                        evaluation.mae
                    ),
                    "holdout_mape": (
                        evaluation.mape
                    ),
                    "rolling_rmse": (
                        mean_metrics.get(
                            "rmse"
                        )
                    ),
                    "selection_rmse": (
                        selection.get(
                            "value"
                        )
                        or
                        evaluation.score
                    ),
                    "best": (
                        evaluation.is_best_model
                    ),
                }
            )

        return sorted(
            records,
            key=lambda item: (
                item["ranking"]
                if item["ranking"] is not None
                else 999999
            )
        )

    # ==========================================
    # GANADOR
    # ==========================================

    @staticmethod
    def _build_winner_data(
        evaluation,
        models_by_id: dict
    ) -> dict:

        if not evaluation:

            return {
                "status": (
                    "No existe evaluación "
                    "disponible"
                )
            }

        model = (
            models_by_id.get(
                evaluation.model_id
            )
        )

        config = (
            evaluation.evaluation_config
            or {}
        )

        selection = (
            config.get(
                "selection",
                {}
            )
        )

        return {
            "model_id": (
                evaluation.model_id
            ),
            "model_type": (
                model.model_type
                if model
                else None
            ),
            "model_version_id": (
                evaluation.model_version_id
            ),
            "evaluation_id": (
                evaluation.id
            ),
            "evaluation_type": (
                evaluation.evaluation_type
            ),
            "ranking_position": (
                evaluation.ranking_position
            ),
            "holdout_mae": (
                evaluation.mae
            ),
            "holdout_rmse": (
                evaluation.rmse
            ),
            "holdout_mape": (
                evaluation.mape
            ),
            "holdout_smape": (
                evaluation.smape
            ),
            "holdout_r2": (
                evaluation.r2
            ),
            "selection_source": (
                selection.get(
                    "source"
                )
            ),
            "selection_value": (
                selection.get(
                    "value"
                )
                or evaluation.score
            ),
        }

    # ==========================================
    # ROLLING ORIGIN
    # ==========================================

    @staticmethod
    def _build_rolling_origin_data(
        evaluation
    ) -> dict:

        if not evaluation:

            return {
                "executed": False,
                "status": (
                    "No existe evaluación"
                )
            }

        config = (
            evaluation.evaluation_config
            or {}
        )

        backtesting = (
            config.get(
                "backtesting",
                {}
            )
        )

        if not backtesting:

            return {
                "executed": False,
                "status": (
                    "La evaluación no contiene "
                    "rolling-origin"
                )
            }

        mean_metrics = (
            backtesting.get(
                "mean_metrics",
                {}
            )
        )

        std_metrics = (
            backtesting.get(
                "std_metrics",
                {}
            )
        )

        return {
            "executed": (
                backtesting.get(
                    "executed",
                    True
                )
            ),
            "strategy": (
                backtesting.get(
                    "strategy"
                )
            ),
            "initial_train_size": (
                backtesting.get(
                    "initial_train_size"
                )
            ),
            "horizon": (
                backtesting.get(
                    "horizon"
                )
            ),
            "step": (
                backtesting.get(
                    "step"
                )
            ),
            "successful_folds": (
                backtesting.get(
                    "successful_folds"
                )
            ),
            "failed_folds": (
                backtesting.get(
                    "failed_folds"
                )
            ),
            "mean_mae": (
                mean_metrics.get(
                    "mae"
                )
            ),
            "mean_rmse": (
                mean_metrics.get(
                    "rmse"
                )
            ),
            "mean_mape": (
                mean_metrics.get(
                    "mape"
                )
            ),
            "mean_smape": (
                mean_metrics.get(
                    "smape"
                )
            ),
            "std_rmse": (
                std_metrics.get(
                    "rmse"
                )
            ),
        }

    # ==========================================
    # DATASET
    # ==========================================

    @staticmethod
    def _dataset_data(
        dataset
    ) -> dict:

        if not dataset:

            return {
                "status": (
                    "Dataset no disponible"
                )
            }

        return {
            "dataset_id": (
                dataset.id
            ),
            "name": (
                dataset.name
            ),
            "file_format": (
                dataset.file_format
            ),
            "source_type": (
                dataset.source_type
            ),
            "processing_stage": (
                dataset.processing_stage
            ),
            "row_count": (
                dataset.row_count
            ),
            "column_count": (
                dataset.column_count
            ),
            "parent_dataset_id": (
                dataset.parent_dataset_id
            ),
            "business_series_id": (
                dataset.business_series_id
            ),
            "created_at": (
                dataset.created_at
            ),
        }

    # ==========================================
    # MODELO ACTIVO
    # ==========================================

    @staticmethod
    def _active_model_data(
        active_model,
        active_version
    ) -> dict:

        if not active_model:

            return {
                "status": (
                    "La serie no tiene "
                    "modelo activo"
                )
            }

        return {
            "model_id": (
                active_model.id
            ),
            "name": (
                active_model.name
            ),
            "model_type": (
                active_model.model_type
            ),
            "logical_version": (
                active_model.version
            ),
            "metric_value": (
                active_model.metric_value
            ),
            "active": (
                active_model.active
            ),
            "active_version_id": (
                active_version.id
                if active_version
                else None
            ),
            "active_version_number": (
                active_version.version_number
                if active_version
                else None
            ),
        }

    # ==========================================
    # PERFORMANCE
    # ==========================================

    def _safe_performance(
        self,
        db: Session,
        business_series_id: int,
        has_active_model: bool
    ) -> dict:

        if not has_active_model:

            return {
                "available": False,
                "reason": (
                    "La serie no tiene "
                    "modelo activo"
                )
            }

        try:

            result = (
                self.performance_service
                .get_business_series_performance(
                    db=db,
                    business_series_id=(
                        business_series_id
                    ),
                    limit=(
                        self.PERFORMANCE_LIMIT
                    ),
                    minimum_observations=(
                        self
                        .PERFORMANCE_MINIMUM_OBSERVATIONS
                    ),
                    rmse_degradation_threshold=(
                        self
                        .RMSE_DEGRADATION_THRESHOLD
                    ),
                    mape_threshold=(
                        self.MAPE_THRESHOLD
                    )
                )
            )

            return {
                "available": True,
                **result,
            }

        except Exception as error:

            try:
                db.rollback()

            except Exception:
                pass

            return {
                "available": False,
                "reason": str(
                    error
                )
            }

    # ==========================================
    # PERFORMANCE DATA
    # ==========================================

    @staticmethod
    def _performance_data(
        performance: dict
    ) -> dict:

        if not performance.get(
            "available"
        ):

            return {
                "status": (
                    performance.get(
                        "reason",
                        "No disponible"
                    )
                )
            }

        metrics = (
            performance.get(
                "metrics"
            )
            or {}
        )

        baseline = (
            performance.get(
                "baseline_metrics"
            )
            or {}
        )

        health = (
            performance.get(
                "health"
            )
        )

        return {
            "model_id": (
                performance.get(
                    "model_id"
                )
            ),
            "model_type": (
                performance.get(
                    "model_type"
                )
            ),
            "observations_available": (
                performance.get(
                    "observations_available"
                )
            ),
            "sufficient_data": (
                performance.get(
                    "sufficient_data"
                )
            ),
            "current_mae": (
                metrics.get(
                    "mae"
                )
            ),
            "current_rmse": (
                metrics.get(
                    "rmse"
                )
            ),
            "current_mape": (
                metrics.get(
                    "mape"
                )
            ),
            "current_smape": (
                metrics.get(
                    "smape"
                )
            ),
            "current_r2": (
                metrics.get(
                    "r2"
                )
            ),
            "baseline_rmse": (
                baseline.get(
                    "rmse"
                )
            ),
            "baseline_mape": (
                baseline.get(
                    "mape"
                )
            ),
            "health": (
                health
            ),
        }

    # ==========================================
    # INVENTARIO
    # ==========================================

    @staticmethod
    def _inventory_sections(
        inventory: dict | None
    ) -> list[dict]:

        if not inventory:

            return []

        return [
            {
                "title": (
                    "9. KPIs de inventario PRE"
                ),
                "type": "key_value",
                "data": (
                    inventory.get(
                        "pre",
                        {}
                    )
                )
            },
            {
                "title": (
                    "10. KPIs de inventario POST"
                ),
                "type": "key_value",
                "data": (
                    inventory.get(
                        "post",
                        {}
                    )
                )
            },
            {
                "title": (
                    "11. Cambios observados "
                    "PRE vs POST"
                ),
                "type": "key_value",
                "data": (
                    inventory.get(
                        "improvement",
                        {}
                    )
                )
            },
        ]

    # ==========================================
    # ESTADÍSTICA SEGURA
    # ==========================================

    def _safe_statistics(
        self,
        db: Session,
        business_series_id: int,
        indicators: list[str],
        alpha: float
    ) -> dict:

        try:

            result = (
                self.statistics_service
                .analyze(
                    db=db,
                    business_series_id=(
                        business_series_id
                    ),
                    indicators=(
                        indicators
                    ),
                    alpha=alpha
                )
            )

            return {
                "available": True,
                **result,
            }

        except HTTPException as error:

            return {
                "available": False,
                "reason": (
                    error.detail
                ),
                "alpha": (
                    alpha
                ),
            }

        except Exception as error:

            try:
                db.rollback()

            except Exception:
                pass

            return {
                "available": False,
                "reason": str(
                    error
                ),
                "alpha": (
                    alpha
                ),
            }

    # ==========================================
    # STATISTICS TEXT
    # ==========================================

    @staticmethod
    def _statistics_text(
        statistics: dict | None
    ) -> str:

        if not statistics:

            return (
                "No se solicitó análisis "
                "estadístico."
            )

        if not statistics.get(
            "available"
        ):

            return (
                "El análisis estadístico "
                "no pudo realizarse: "
                f"{statistics.get('reason')}"
            )

        return (
            "Nivel de significancia "
            f"α={statistics.get('alpha')}. "
            f"Método de emparejamiento: "
            f"{statistics.get('pairing_method')}. "
            f"Pares analizados: "
            f"{statistics.get('paired_observations')}."
        )

    # ==========================================
    # STATISTICS RECORDS
    # ==========================================

    @staticmethod
    def _statistics_records(
        statistics: dict | None
    ) -> list[dict]:

        if (
            not statistics
            or not statistics.get(
                "available"
            )
        ):

            return []

        records = []

        for item in (
            statistics.get(
                "indicators",
                []
            )
        ):

            pre = (
                item.get(
                    "pre",
                    {}
                )
                .get(
                    "descriptive",
                    {}
                )
            )

            post = (
                item.get(
                    "post",
                    {}
                )
                .get(
                    "descriptive",
                    {}
                )
            )

            selected_test = (
                item.get(
                    "selected_test",
                    {}
                )
            )

            records.append(
                {
                    "indicator": (
                        item.get(
                            "indicator_label"
                        )
                        or
                        item.get(
                            "indicator"
                        )
                    ),
                    "pairs": (
                        item.get(
                            "paired_observations"
                        )
                    ),
                    "pre_mean": (
                        pre.get(
                            "mean"
                        )
                    ),
                    "post_mean": (
                        post.get(
                            "mean"
                        )
                    ),
                    "difference_mean": (
                        item.get(
                            "difference_mean"
                        )
                    ),
                    "improvement_percent": (
                        item.get(
                            "improvement_percent"
                        )
                    ),
                    "direction": (
                        item.get(
                            "direction"
                        )
                    ),
                    "test": (
                        selected_test.get(
                            "test"
                        )
                    ),
                    "p_value": (
                        selected_test.get(
                            "p_value"
                        )
                    ),
                    "significant": (
                        selected_test.get(
                            "significant"
                        )
                    ),
                }
            )

        return records

    # ==========================================
    # INTERPRETACIÓN
    # ==========================================

    @staticmethod
    def _build_interpretation(
        inventory: dict | None,
        statistics: dict | None,
        performance: dict | None
    ) -> str:

        messages = []

        if inventory:

            improvement = (
                inventory.get(
                    "improvement",
                    {}
                )
            )

            stockout_reduction = (
                improvement.get(
                    "stockout_units_reduction_percent"
                )
            )

            service_improvement = (
                improvement.get(
                    "service_level_improvement_points"
                )
            )

            if stockout_reduction is not None:

                messages.append(
                    (
                        "La comparación descriptiva "
                        "muestra una variación de "
                        f"{stockout_reduction:.2f}% "
                        "en la reducción de unidades "
                        "en quiebre de stock."
                    )
                )

            if service_improvement is not None:

                messages.append(
                    (
                        "El nivel de servicio "
                        "presentó una diferencia "
                        f"de {service_improvement:.2f} "
                        "puntos porcentuales entre "
                        "los periodos analizados."
                    )
                )

        if (
            statistics
            and statistics.get(
                "available"
            )
        ):

            significant_count = sum(
                1
                for item
                in statistics.get(
                    "indicators",
                    []
                )
                if (
                    item.get(
                        "selected_test",
                        {}
                    )
                    .get(
                        "significant"
                    )
                    is True
                )
            )

            total = len(
                statistics.get(
                    "indicators",
                    []
                )
            )

            messages.append(
                (
                    "El análisis inferencial "
                    f"identificó {significant_count} "
                    "indicadores con diferencias "
                    "estadísticamente significativas "
                    f"de un total de {total} "
                    "indicadores analizados."
                )
            )

        if (
            performance
            and performance.get(
                "available"
            )
        ):

            observations = (
                performance.get(
                    "observations_available",
                    0
                )
            )

            messages.append(
                (
                    "El desempeño productivo "
                    "se evaluó utilizando "
                    f"{observations} observaciones "
                    "con valores reales disponibles."
                )
            )

        messages.append(
            (
                "Las diferencias descritas deben "
                "interpretarse dentro del diseño "
                "metodológico de la investigación "
                "y no constituyen, por sí solas, "
                "evidencia causal."
            )
        )

        return " ".join(
            messages
        )