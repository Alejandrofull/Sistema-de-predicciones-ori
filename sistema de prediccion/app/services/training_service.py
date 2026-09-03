from __future__ import annotations

from pathlib import Path
from tempfile import (
    NamedTemporaryFile,
    TemporaryDirectory,
)
from time import perf_counter
from uuid import uuid4

import joblib

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.data.validation.dataset_validator import (
    DatasetValidator,
)

from app.integrations.supabase.storage_service import (
    SupabaseStorageService,
)

from app.ml.trainer import (
    ModelTrainer,
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

from app.repositories.training_repository import (
    TrainingRepository,
)

from app.services.import_service import (
    ImportService,
)


class TrainingService:

    SUPPORTED_MODELS = {
        "arima",
        "random_forest",
        "xgboost",
        "hybrid",
    }

    # ==========================================
    # CONFIGURACIÓN BACKTESTING
    # ==========================================

    BACKTEST_HORIZON = 1
    BACKTEST_STEP = 1
    BACKTEST_MAX_FOLDS = 5

    def __init__(self):

        # ==========================================
        # STORAGE DATASETS
        # ==========================================

        self.dataset_storage = (
            SupabaseStorageService(
                bucket="datasets"
            )
        )

        # ==========================================
        # STORAGE MODELOS
        # ==========================================

        self.model_storage = (
            SupabaseStorageService(
                bucket="models"
            )
        )

        # ==========================================
        # SERVICIOS
        # ==========================================

        self.import_service = (
            ImportService()
        )

        self.validator = (
            DatasetValidator()
        )

        self.trainer = (
            ModelTrainer()
        )

    # ==========================================
    # ENTRENAMIENTO PRINCIPAL
    # ==========================================

    def train_models(
        self,
        db: Session,
        dataset_id: int,
        user_id: int,
        date_column: str | None,
        target_column: str | None,
        model_names: list[str],
        test_ratio: float
    ) -> dict:

        # ==========================================
        # 1. DATASET
        # ==========================================

        dataset = (
            DatasetRepository.get_by_id(
                db,
                dataset_id
            )
        )

        if not dataset:

            raise HTTPException(
                status_code=404,
                detail="Dataset no encontrado"
            )

        if dataset.user_id != user_id:

            raise HTTPException(
                status_code=403,
                detail=(
                    "No tiene acceso "
                    "a este dataset"
                )
            )

        if not dataset.storage_path:

            raise HTTPException(
                status_code=400,
                detail=(
                    "El dataset no tiene "
                    "archivo asociado"
                )
            )

        if not dataset.file_format:

            raise HTTPException(
                status_code=400,
                detail=(
                    "El dataset no tiene "
                    "formato registrado"
                )
            )

        if (
            dataset.processing_stage
            != "features"
        ):

            raise HTTPException(
                status_code=400,
                detail=(
                    "El entrenamiento requiere "
                    "un dataset con "
                    "processing_stage='features'"
                )
            )

        # ==========================================
        # 2. MODELOS
        # ==========================================

        normalized_model_names = (
            self._normalize_model_names(
                model_names
            )
        )

        # ==========================================
        # 3. TEST RATIO
        # ==========================================

        if not (
            0.05
            <= test_ratio
            <= 0.40
        ):

            raise HTTPException(
                status_code=400,
                detail=(
                    "test_ratio debe estar "
                    "entre 0.05 y 0.40"
                )
            )

        # ==========================================
        # 4. CARGAR DATASET
        # ==========================================

        dataframe = (
            self._load_dataset(
                storage_path=(
                    dataset.storage_path
                ),
                file_format=(
                    dataset.file_format
                )
            )
        )

        if dataframe.empty:

            raise HTTPException(
                status_code=400,
                detail=(
                    "El dataset no contiene "
                    "registros para entrenar"
                )
            )

        # ==========================================
        # 5. ANALIZAR DATASET
        # ==========================================

        validation = (
            self.validator.analyze(
                dataframe
            )
        )

        metadata = (
            dataset.dataset_metadata
            or {}
        )

        # ==========================================
        # 6. COLUMNA FECHA
        # ==========================================

        resolved_date_column = (
            date_column
            or metadata.get(
                "date_column"
            )
            or validation.get(
                "date_column"
            )
        )

        # ==========================================
        # 7. TARGET
        # ==========================================

        resolved_target_column = (
            target_column
            or metadata.get(
                "target_column"
            )
            or validation.get(
                "target_column"
            )
        )

        if not resolved_date_column:

            raise HTTPException(
                status_code=400,
                detail=(
                    "No se pudo determinar "
                    "la columna de fecha"
                )
            )

        if not resolved_target_column:

            raise HTTPException(
                status_code=400,
                detail=(
                    "No se pudo determinar "
                    "la variable objetivo"
                )
            )

        if (
            resolved_date_column
            not in dataframe.columns
        ):

            raise HTTPException(
                status_code=400,
                detail=(
                    "La columna de fecha "
                    f"'{resolved_date_column}' "
                    "no existe en el dataset"
                )
            )

        if (
            resolved_target_column
            not in dataframe.columns
        ):

            raise HTTPException(
                status_code=400,
                detail=(
                    "La variable objetivo "
                    f"'{resolved_target_column}' "
                    "no existe en el dataset"
                )
            )

        # ==========================================
        # 8. BUSINESS SERIES
        # ==========================================

        business_series_id = (
            dataset.business_series_id
        )

        # ==========================================
        # 9. VARIABLES EXTERNAS
        # ==========================================

        external_variables = (
            metadata.get(
                "external_variables"
            )
            or []
        )

        # ==========================================
        # 10. RESULTADOS
        # ==========================================

        successful = {}

        errors = {}

        # ==========================================
        # 11. ENTRENAR CADA MODELO
        # ==========================================

        for model_name in (
            normalized_model_names
        ):

            artifact_path = None

            training = None

            try:

                # ==================================
                # MODELO LÓGICO
                # ==================================

                model_display_name = (
                    self._build_model_name(
                        dataset_name=(
                            dataset.name
                        ),
                        model_name=(
                            model_name
                        ),
                        business_series_id=(
                            business_series_id
                        )
                    )
                )

                ml_model = (
                    ModelRepository
                    .get_or_create(
                        db=db,
                        name=(
                            model_display_name
                        ),
                        model_type=(
                            model_name
                        ),
                        business_series_id=(
                            business_series_id
                        )
                    )
                )

                # ==================================
                # TRAINING
                # ==================================

                training = (
                    TrainingRepository.create(
                        db=db,
                        dataset_id=(
                            dataset.id
                        ),
                        model_id=(
                            ml_model.id
                        ),
                        status="pending"
                    )
                )

                TrainingRepository.mark_running(
                    db=db,
                    training=training
                )

                # ==================================
                # CRONÓMETRO TOTAL
                # ==================================

                start_time = (
                    perf_counter()
                )

                # ==================================
                # HOLDOUT TEMPORAL
                # ==================================

                result = (
                    self.trainer
                    .train_and_evaluate(
                        dataframe=(
                            dataframe
                        ),
                        date_column=(
                            resolved_date_column
                        ),
                        target_column=(
                            resolved_target_column
                        ),
                        model_name=(
                            model_name
                        ),
                        test_ratio=(
                            test_ratio
                        )
                    )
                )

                model_object = (
                    result[
                        "model_object"
                    ]
                )

                evaluation = (
                    result[
                        "evaluation"
                    ]
                )

                holdout_metrics = (
                    evaluation[
                        "metrics"
                    ]
                )

                holdout_rmse = (
                    holdout_metrics.get(
                        "rmse"
                    )
                )

                if holdout_rmse is None:

                    raise RuntimeError(
                        "El entrenamiento no "
                        "generó una métrica RMSE"
                    )

                # ==================================
                # ROLLING-ORIGIN BACKTEST
                # ==================================

                backtest = None

                backtest_error = None

                try:

                    backtest = (
                        self.trainer
                        .rolling_origin_backtest(
                            dataframe=(
                                dataframe
                            ),
                            date_column=(
                                resolved_date_column
                            ),
                            target_column=(
                                resolved_target_column
                            ),
                            model_name=(
                                model_name
                            ),
                            initial_train_size=None,
                            horizon=(
                                self
                                .BACKTEST_HORIZON
                            ),
                            step=(
                                self
                                .BACKTEST_STEP
                            ),
                            max_folds=(
                                self
                                .BACKTEST_MAX_FOLDS
                            )
                        )
                    )

                except Exception as error:

                    backtest_error = str(
                        error
                    )

                # ==================================
                # MÉTRICA PARA SELECCIÓN
                # ==================================

                selection_rmse = float(
                    holdout_rmse
                )

                selection_source = (
                    "holdout_rmse"
                )

                if backtest:

                    mean_rmse = (
                        backtest
                        .get(
                            "mean_metrics",
                            {}
                        )
                        .get(
                            "rmse"
                        )
                    )

                    if mean_rmse is not None:

                        selection_rmse = float(
                            mean_rmse
                        )

                        selection_source = (
                            "rolling_origin_mean_rmse"
                        )

                # ==================================
                # TIEMPO TOTAL
                # ==================================

                elapsed = (
                    perf_counter()
                    -
                    start_time
                )

                # ==================================
                # FEATURES
                # ==================================

                feature_columns = (
                    evaluation.get(
                        "feature_columns",
                        []
                    )
                    or []
                )

                external_feature_columns = (
                    self
                    ._get_external_feature_columns(
                        feature_columns
                    )
                )

                model_external_variables = (
                    self
                    ._filter_external_variables(
                        external_variables=(
                            external_variables
                        ),
                        feature_columns=(
                            external_feature_columns
                        )
                    )
                )

                # ==================================
                # VERSIÓN
                # ==================================

                version_number = (
                    ModelVersionRepository
                    .get_next_version_number(
                        db=db,
                        model_id=(
                            ml_model.id
                        )
                    )
                )

                # ==================================
                # ARTEFACTO
                # ==================================

                artifact_path = (
                    self._save_model_artifact(
                        model_object=(
                            model_object
                        ),
                        dataset_id=(
                            dataset.id
                        ),
                        model_id=(
                            ml_model.id
                        ),
                        model_name=(
                            model_name
                        ),
                        version_number=(
                            version_number
                        )
                    )
                )

                # ==================================
                # FEATURE CONFIG
                # ==================================

                feature_config = {
                    "date_column": (
                        resolved_date_column
                    ),
                    "target_column": (
                        resolved_target_column
                    ),
                    "feature_columns": (
                        feature_columns
                    ),
                    "external_feature_columns": (
                        external_feature_columns
                    ),
                    "external_variables": (
                        model_external_variables
                    ),
                    "uses_external_variables": (
                        len(
                            external_feature_columns
                        )
                        > 0
                    ),
                    "test_ratio": float(
                        test_ratio
                    ),
                    "processing_stage": (
                        dataset.processing_stage
                    ),
                    "dataset_id": (
                        dataset.id
                    ),
                    "parent_dataset_id": (
                        dataset.parent_dataset_id
                    ),
                    "business_series_id": (
                        business_series_id
                    ),
                    "dataset_source_type": (
                        dataset.source_type
                    ),
                    "evaluation_strategy": {
                        "holdout": True,
                        "rolling_origin": (
                            backtest
                            is not None
                        ),
                        "selection_metric": (
                            selection_source
                        ),
                    },
                }

                # ==================================
                # CREAR MODEL VERSION
                # ==================================

                version = (
                    ModelVersionRepository.create(
                        db=db,
                        model_id=(
                            ml_model.id
                        ),
                        version_number=(
                            version_number
                        ),
                        parameters=(
                            evaluation.get(
                                "parameters"
                            )
                        ),
                        feature_config=(
                            feature_config
                        ),
                        artifact_path=(
                            artifact_path
                        ),
                        is_active=False
                    )
                )

                # ==================================
                # ACTUALIZAR MODELO LÓGICO
                #
                # Guardamos la métrica utilizada
                # realmente para seleccionar.
                # ==================================

                ModelRepository.update_training_result(
                    db=db,
                    model=(
                        ml_model
                    ),
                    version=str(
                        version_number
                    ),
                    metric_value=float(
                        selection_rmse
                    )
                )

                # ==================================
                # COMPLETAR TRAINING
                # ==================================

                TrainingRepository.mark_completed(
                    db=db,
                    training=(
                        training
                    ),
                    model_id=(
                        ml_model.id
                    )
                )

                # ==================================
                # CONFIG BACKTEST PARA JSON
                # ==================================

                backtest_config = (
                    self._build_backtest_config(
                        backtest=backtest,
                        error=backtest_error
                    )
                )

                # ==================================
                # MODEL EVALUATION
                #
                # Las columnas mae/rmse/etc.
                # mantienen HOLDOUT para conservar
                # compatibilidad con monitoring.
                #
                # Rolling-origin queda almacenado
                # dentro de evaluation_config.
                # ==================================

                model_evaluation = (
                    ModelEvaluationRepository.create(
                        db=db,
                        model_id=(
                            ml_model.id
                        ),
                        model_version_id=(
                            version.id
                        ),
                        training_id=(
                            training.id
                        ),
                        dataset_id=(
                            dataset.id
                        ),
                        evaluation_type=(
                            "holdout_temporal_"
                            "with_rolling_origin"
                        ),
                        mae=(
                            holdout_metrics.get(
                                "mae"
                            )
                        ),
                        mse=(
                            holdout_metrics.get(
                                "mse"
                            )
                        ),
                        rmse=(
                            holdout_metrics.get(
                                "rmse"
                            )
                        ),
                        mape=(
                            holdout_metrics.get(
                                "mape"
                            )
                        ),
                        smape=(
                            holdout_metrics.get(
                                "smape"
                            )
                        ),
                        r2=(
                            holdout_metrics.get(
                                "r2"
                            )
                        ),
                        training_time_seconds=(
                            float(
                                elapsed
                            )
                        ),
                        prediction_time_seconds=None,
                        score=(
                            float(
                                selection_rmse
                            )
                        ),
                        ranking_position=None,
                        is_best_model=False,
                        evaluation_config={
                            "selection": {
                                "metric": (
                                    "rmse"
                                ),
                                "source": (
                                    selection_source
                                ),
                                "value": float(
                                    selection_rmse
                                ),
                            },
                            "holdout": {
                                "strategy": (
                                    "temporal_holdout"
                                ),
                                "test_ratio": float(
                                    test_ratio
                                ),
                                "training_rows": (
                                    evaluation[
                                        "dataset"
                                    ][
                                        "training_rows"
                                    ]
                                ),
                                "testing_rows": (
                                    evaluation[
                                        "dataset"
                                    ][
                                        "testing_rows"
                                    ]
                                ),
                                "total_rows": (
                                    evaluation[
                                        "dataset"
                                    ].get(
                                        "total_rows"
                                    )
                                ),
                                "metrics": (
                                    self
                                    ._serialize_metrics(
                                        holdout_metrics
                                    )
                                ),
                            },
                            "backtesting": (
                                backtest_config
                            ),
                            "date_column": (
                                resolved_date_column
                            ),
                            "target_column": (
                                resolved_target_column
                            ),
                            "feature_columns": (
                                feature_columns
                            ),
                            "external_feature_columns": (
                                external_feature_columns
                            ),
                            "external_variables": (
                                model_external_variables
                            ),
                            "business_series_id": (
                                business_series_id
                            ),
                            "dataset_id": (
                                dataset.id
                            ),
                        },
                        notes=(
                            "Evaluación mediante "
                            "holdout temporal y "
                            "rolling-origin con "
                            "ventana expansiva."
                            if backtest
                            else (
                                "Evaluación mediante "
                                "holdout temporal. "
                                "El rolling-origin "
                                "no pudo completarse: "
                                f"{backtest_error}"
                            )
                        )
                    )
                )

                # ==================================
                # RESULTADO TEMPORAL
                # ==================================

                successful[
                    model_name
                ] = {
                    "training": (
                        training
                    ),
                    "model": (
                        ml_model
                    ),
                    "version": (
                        version
                    ),
                    "evaluation": (
                        model_evaluation
                    ),
                    "metrics": (
                        holdout_metrics
                    ),
                    "backtest": (
                        backtest
                    ),
                    "backtest_error": (
                        backtest_error
                    ),
                    "selection_rmse": float(
                        selection_rmse
                    ),
                    "selection_source": (
                        selection_source
                    ),
                    "elapsed": float(
                        elapsed
                    ),
                    "artifact_path": (
                        artifact_path
                    ),
                    "feature_columns": (
                        feature_columns
                    ),
                    "external_feature_columns": (
                        external_feature_columns
                    ),
                }

            except Exception as error:

                # ==================================
                # TRAINING FALLIDO
                # ==================================

                if training is not None:

                    try:

                        TrainingRepository.mark_failed(
                            db=db,
                            training=(
                                training
                            )
                        )

                    except Exception:
                        pass

                # ==================================
                # ARTEFACTO HUÉRFANO
                # ==================================

                if artifact_path:

                    try:

                        self.model_storage.remove_file(
                            artifact_path
                        )

                    except Exception:
                        pass

                errors[
                    model_name
                ] = str(
                    error
                )

        # ==========================================
        # 12. ALGÚN MODELO DEBE FUNCIONAR
        # ==========================================

        if not successful:

            raise HTTPException(
                status_code=500,
                detail={
                    "message": (
                        "Ningún modelo pudo "
                        "entrenarse correctamente"
                    ),
                    "errors": (
                        errors
                    )
                }
            )

        # ==========================================
        # 13. RANKING ROBUSTO
        #
        # Prioridad:
        # rolling-origin mean RMSE
        #
        # Fallback:
        # holdout RMSE
        # ==========================================

        ranking = sorted(
            successful.keys(),
            key=lambda name: (
                float(
                    successful[
                        name
                    ][
                        "selection_rmse"
                    ]
                )
            )
        )

        winner = (
            ranking[
                0
            ]
        )

        # ==========================================
        # 14. GUARDAR RANKING
        # ==========================================

        response_results = []

        for (
            position,
            model_name
        ) in enumerate(
            ranking,
            start=1
        ):

            item = (
                successful[
                    model_name
                ]
            )

            model_evaluation = (
                item[
                    "evaluation"
                ]
            )

            ModelEvaluationRepository.update_ranking(
                db=db,
                evaluation=(
                    model_evaluation
                ),
                ranking_position=(
                    position
                ),
                is_best_model=(
                    position == 1
                )
            )

            backtest = (
                item.get(
                    "backtest"
                )
            )

            backtest_summary = None

            if backtest:

                backtest_summary = {
                    "strategy": (
                        backtest.get(
                            "strategy"
                        )
                    ),
                    "horizon": (
                        backtest.get(
                            "horizon"
                        )
                    ),
                    "step": (
                        backtest.get(
                            "step"
                        )
                    ),
                    "successful_folds": (
                        backtest.get(
                            "successful_folds"
                        )
                    ),
                    "failed_folds": (
                        backtest.get(
                            "failed_folds"
                        )
                    ),
                    "mean_metrics": (
                        backtest.get(
                            "mean_metrics"
                        )
                    ),
                    "std_metrics": (
                        backtest.get(
                            "std_metrics"
                        )
                    ),
                }

            response_results.append(
                {
                    "training_id": (
                        item[
                            "training"
                        ].id
                    ),
                    "model_id": (
                        item[
                            "model"
                        ].id
                    ),
                    "model_version_id": (
                        item[
                            "version"
                        ].id
                    ),
                    "model_name": (
                        model_name
                    ),
                    "model_type": (
                        item[
                            "model"
                        ].model_type
                    ),
                    "version_number": (
                        item[
                            "version"
                        ].version_number
                    ),
                    "artifact_path": (
                        item[
                            "artifact_path"
                        ]
                    ),

                    # Holdout
                    "metrics": (
                        item[
                            "metrics"
                        ]
                    ),

                    # Rolling-origin
                    "backtesting": (
                        backtest_summary
                    ),
                    "backtesting_error": (
                        item[
                            "backtest_error"
                        ]
                    ),

                    # Métrica realmente usada
                    # para el ranking.
                    "selection": {
                        "metric": "rmse",
                        "source": (
                            item[
                                "selection_source"
                            ]
                        ),
                        "value": (
                            item[
                                "selection_rmse"
                            ]
                        ),
                    },

                    "ranking_position": (
                        position
                    ),
                    "is_best_model": (
                        position == 1
                    ),
                    "training_time_seconds": (
                        item[
                            "elapsed"
                        ]
                    )
                }
            )

        # ==========================================
        # 15. GANADOR
        # ==========================================

        winner_item = (
            successful[
                winner
            ]
        )

        winner_model = (
            winner_item[
                "model"
            ]
        )

        # ==========================================
        # 16. RESPUESTA
        # ==========================================

        return {
            "dataset_id": (
                dataset.id
            ),
            "business_series_id": (
                business_series_id
            ),
            "winner": (
                winner
            ),
            "winner_model_id": (
                winner_model.id
            ),
            "ranking": (
                ranking
            ),
            "ranking_metric": (
                "rolling_origin_mean_rmse"
                if winner_item[
                    "selection_source"
                ]
                == "rolling_origin_mean_rmse"
                else "holdout_rmse"
            ),
            "winner_selection_rmse": (
                winner_item[
                    "selection_rmse"
                ]
            ),
            "results": (
                response_results
            ),
            "errors": (
                errors
            )
        }

    # ==========================================
    # CONFIG BACKTESTING PARA JSON
    # ==========================================

    @classmethod
    def _build_backtest_config(
        cls,
        backtest: dict | None,
        error: str | None
    ) -> dict:

        if not backtest:

            return {
                "executed": False,
                "strategy": (
                    "rolling_origin_"
                    "expanding_window"
                ),
                "horizon": (
                    cls.BACKTEST_HORIZON
                ),
                "step": (
                    cls.BACKTEST_STEP
                ),
                "max_folds": (
                    cls.BACKTEST_MAX_FOLDS
                ),
                "error": error,
            }

        folds = []

        for fold in (
            backtest.get(
                "folds",
                []
            )
        ):

            folds.append(
                {
                    "fold": (
                        fold.get(
                            "fold"
                        )
                    ),
                    "training_rows": (
                        fold.get(
                            "training_rows"
                        )
                    ),
                    "testing_rows": (
                        fold.get(
                            "testing_rows"
                        )
                    ),
                    "train_start_date": (
                        fold.get(
                            "train_start_date"
                        )
                    ),
                    "train_end_date": (
                        fold.get(
                            "train_end_date"
                        )
                    ),
                    "test_start_date": (
                        fold.get(
                            "test_start_date"
                        )
                    ),
                    "test_end_date": (
                        fold.get(
                            "test_end_date"
                        )
                    ),
                    "metrics": (
                        cls._serialize_metrics(
                            fold.get(
                                "metrics",
                                {}
                            )
                        )
                    ),
                }
            )

        return {
            "executed": True,
            "strategy": (
                backtest.get(
                    "strategy"
                )
            ),
            "initial_train_size": (
                backtest.get(
                    "initial_train_size"
                )
            ),
            "horizon": (
                backtest.get(
                    "horizon"
                )
            ),
            "step": (
                backtest.get(
                    "step"
                )
            ),
            "max_folds": (
                backtest.get(
                    "requested_max_folds"
                )
            ),
            "successful_folds": (
                backtest.get(
                    "successful_folds"
                )
            ),
            "failed_folds": (
                backtest.get(
                    "failed_folds"
                )
            ),
            "mean_metrics": (
                cls._serialize_metrics(
                    backtest.get(
                        "mean_metrics",
                        {}
                    )
                )
            ),
            "std_metrics": (
                cls._serialize_metrics(
                    backtest.get(
                        "std_metrics",
                        {}
                    )
                )
            ),
            "min_metrics": (
                cls._serialize_metrics(
                    backtest.get(
                        "min_metrics",
                        {}
                    )
                )
            ),
            "max_metrics": (
                cls._serialize_metrics(
                    backtest.get(
                        "max_metrics",
                        {}
                    )
                )
            ),
            "folds": (
                folds
            ),
            "methodological_note": (
                backtest.get(
                    "methodological_note"
                )
            ),
            "errors": (
                backtest.get(
                    "errors",
                    []
                )
            ),
        }

    # ==========================================
    # SERIALIZAR MÉTRICAS
    # ==========================================

    @staticmethod
    def _serialize_metrics(
        metrics: dict | None
    ) -> dict:

        if not metrics:

            return {}

        result = {}

        for key, value in (
            metrics.items()
        ):

            if value is None:

                result[
                    key
                ] = None

                continue

            if isinstance(
                value,
                bool
            ):

                result[
                    key
                ] = value

                continue

            try:

                result[
                    key
                ] = float(
                    value
                )

            except (
                TypeError,
                ValueError,
            ):

                result[
                    key
                ] = value

        return result

    # ==========================================
    # CARGAR DATASET
    # ==========================================

    def _load_dataset(
        self,
        storage_path: str,
        file_format: str
    ):

        try:

            # Los datasets están en
            # bucket "datasets".

            file_bytes = (
                self.dataset_storage
                .download_bytes(
                    storage_path
                )
            )

        except Exception as error:

            raise HTTPException(
                status_code=500,
                detail=(
                    "No se pudo descargar "
                    "el dataset desde Storage: "
                    f"{error}"
                )
            )

        temp_path = None

        normalized_format = (
            file_format
            .lower()
            .strip()
            .lstrip(".")
        )

        try:

            with NamedTemporaryFile(
                delete=False,
                suffix=(
                    f".{normalized_format}"
                )
            ) as tmp:

                tmp.write(
                    file_bytes
                )

                temp_path = Path(
                    tmp.name
                )

            return (
                self.import_service.load(
                    normalized_format,
                    temp_path
                )
            )

        finally:

            if temp_path:

                temp_path.unlink(
                    missing_ok=True
                )

    # ==========================================
    # GUARDAR ARTEFACTO
    # ==========================================

    def _save_model_artifact(
        self,
        model_object,
        dataset_id: int,
        model_id: int,
        model_name: str,
        version_number: int
    ) -> str:

        with TemporaryDirectory() as tmp_dir:

            artifact_filename = (
                f"{model_name}_"
                f"v{version_number}"
                ".joblib"
            )

            local_path = (
                Path(
                    tmp_dir
                )
                /
                artifact_filename
            )

            joblib.dump(
                model_object,
                local_path
            )

            remote_path = (
                f"dataset_{dataset_id}/"
                f"model_{model_id}/"
                f"version_{version_number}/"
                f"{uuid4()}_"
                f"{artifact_filename}"
            )

            self.model_storage.upload_file(
                local_path=(
                    local_path
                ),
                remote_path=(
                    remote_path
                ),
                content_type=(
                    "application/octet-stream"
                )
            )

            return remote_path

    # ==========================================
    # NOMBRE MODELO
    # ==========================================

    @staticmethod
    def _build_model_name(
        dataset_name: str,
        model_name: str,
        business_series_id: int | None
    ) -> str:

        if business_series_id is None:

            return (
                f"{dataset_name}_"
                f"{model_name}"
            )[:100]

        return (
            f"series_"
            f"{business_series_id}_"
            f"{model_name}"
        )[:100]

    # ==========================================
    # NORMALIZAR MODELOS
    # ==========================================

    @classmethod
    def _normalize_model_names(
        cls,
        model_names: list[str]
    ) -> list[str]:

        if not model_names:

            raise HTTPException(
                status_code=400,
                detail=(
                    "Debe seleccionar "
                    "al menos un modelo"
                )
            )

        normalized = []

        for model_name in model_names:

            value = (
                str(
                    model_name
                )
                .strip()
                .lower()
            )

            if (
                value
                not in cls.SUPPORTED_MODELS
            ):

                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Modelo no soportado: "
                        f"{value}"
                    )
                )

            if value not in normalized:

                normalized.append(
                    value
                )

        return normalized

    # ==========================================
    # FEATURES EXTERNAS
    # ==========================================

    @staticmethod
    def _get_external_feature_columns(
        feature_columns: list[str]
    ) -> list[str]:

        return [
            column
            for column
            in feature_columns
            if (
                isinstance(
                    column,
                    str
                )
                and column.startswith(
                    "ext_"
                )
            )
        ]

    # ==========================================
    # VARIABLES EXTERNAS
    # ==========================================

    @staticmethod
    def _filter_external_variables(
        external_variables: list,
        feature_columns: list[str]
    ) -> list[dict]:

        if not external_variables:

            return []

        if not feature_columns:

            return []

        feature_set = set(
            feature_columns
        )

        result = []

        for variable in external_variables:

            if not isinstance(
                variable,
                dict
            ):

                continue

            feature_name = (
                variable.get(
                    "feature_name"
                )
            )

            if (
                feature_name
                not in feature_set
            ):

                continue

            result.append(
                {
                    "variable_id": (
                        variable.get(
                            "variable_id"
                        )
                    ),
                    "name": (
                        variable.get(
                            "name"
                        )
                    ),
                    "variable_type": (
                        variable.get(
                            "variable_type"
                        )
                    ),
                    "source_type": (
                        variable.get(
                            "source_type"
                        )
                    ),
                    "feature_name": (
                        feature_name
                    ),
                    "business_key": (
                        variable.get(
                            "business_key"
                        )
                    ),
                }
            )

        return result