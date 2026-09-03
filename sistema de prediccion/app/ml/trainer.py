from __future__ import annotations

import math

from statistics import (
    mean,
    stdev,
)

from typing import Any

import numpy as np
import pandas as pd

from app.ml.models.arima.model import (
    ArimaDemandModel,
)

from app.ml.models.hybrid.model import (
    HybridDemandModel,
)

from app.ml.models.random_forest.model import (
    RandomForestDemandModel,
)

from app.ml.models.xgboost.model import (
    XGBoostDemandModel,
)


class ModelTrainer:

    SUPPORTED_MODELS = {
        "arima",
        "random_forest",
        "xgboost",
        "hybrid",
    }

    METRIC_NAMES = (
        "mae",
        "mse",
        "rmse",
        "mape",
        "smape",
        "r2",
    )

    # ==========================================
    # TRAIN + HOLDOUT TEMPORAL
    #
    # Se conserva porque TrainingService
    # actualmente depende de este método.
    # ==========================================

    def train_and_evaluate(
        self,
        dataframe: pd.DataFrame,
        date_column: str,
        target_column: str,
        model_name: str,
        test_ratio: float = 0.20
    ) -> dict[str, Any]:

        model_name = (
            self._normalize_model_name(
                model_name
            )
        )

        if not (
            0.05
            <= test_ratio
            <= 0.40
        ):
            raise ValueError(
                "test_ratio debe estar "
                "entre 0.05 y 0.40"
            )

        df = self._prepare_dataframe(
            dataframe=dataframe,
            date_column=date_column,
            target_column=target_column
        )

        if len(df) < 30:

            raise ValueError(
                "Se requieren al menos "
                "30 registros para entrenar "
                "y evaluar un modelo"
            )

        split_index = int(
            len(df)
            *
            (
                1
                -
                test_ratio
            )
        )

        if split_index <= 0:

            raise ValueError(
                "El conjunto de entrenamiento "
                "quedó vacío"
            )

        train_df = (
            df
            .iloc[
                :split_index
            ]
            .copy()
        )

        test_df = (
            df
            .iloc[
                split_index:
            ]
            .copy()
        )

        if train_df.empty:

            raise ValueError(
                "El conjunto de entrenamiento "
                "está vacío"
            )

        if test_df.empty:

            raise ValueError(
                "El conjunto de prueba "
                "está vacío"
            )

        feature_columns = (
            []
            if model_name == "arima"
            else self._get_feature_columns(
                df=df,
                date_column=date_column,
                target_column=target_column
            )
        )

        result = (
            self._evaluate_split(
                train_df=train_df,
                test_df=test_df,
                date_column=date_column,
                target_column=target_column,
                model_name=model_name,
                feature_columns=(
                    feature_columns
                )
            )
        )

        model = (
            result[
                "model_object"
            ]
        )

        evaluation = (
            result[
                "evaluation"
            ]
        )

        evaluation[
            "dataset"
        ] = {
            "total_rows": int(
                len(df)
            ),
            "training_rows": int(
                len(train_df)
            ),
            "testing_rows": int(
                len(test_df)
            ),
            "test_ratio": float(
                test_ratio
            ),
            "date_column": (
                date_column
            ),
            "target_column": (
                target_column
            ),
            "evaluation_strategy": (
                "temporal_holdout"
            ),
        }

        evaluation[
            "test_dates"
        ] = [
            value.isoformat()
            for value
            in test_df[
                date_column
            ]
        ]

        evaluation[
            "actual_values"
        ] = [
            float(
                value
            )
            for value
            in test_df[
                target_column
            ]
        ]

        evaluation[
            "feature_columns"
        ] = (
            feature_columns
        )

        return {
            "model_object": (
                model
            ),
            "evaluation": (
                evaluation
            )
        }

    # ==========================================
    # COMPARAR HOLDOUT
    #
    # Se conserva para compatibilidad.
    # ==========================================

    def compare_all(
        self,
        dataframe: pd.DataFrame,
        date_column: str,
        target_column: str,
        test_ratio: float = 0.20
    ) -> dict[str, Any]:

        results = {}
        errors = {}
        model_objects = {}

        for model_name in [
            "arima",
            "random_forest",
            "xgboost",
            "hybrid",
        ]:

            try:

                result = (
                    self.train_and_evaluate(
                        dataframe=dataframe,
                        date_column=date_column,
                        target_column=target_column,
                        model_name=model_name,
                        test_ratio=test_ratio
                    )
                )

                results[
                    model_name
                ] = (
                    result[
                        "evaluation"
                    ]
                )

                model_objects[
                    model_name
                ] = (
                    result[
                        "model_object"
                    ]
                )

            except Exception as error:

                errors[
                    model_name
                ] = str(
                    error
                )

        if not results:

            raise RuntimeError(
                "Ningún modelo pudo "
                "ser entrenado correctamente"
            )

        ranking = sorted(
            results.keys(),
            key=lambda name: (
                self._safe_ranking_metric(
                    results[
                        name
                    ][
                        "metrics"
                    ].get(
                        "rmse"
                    )
                )
            )
        )

        winner = (
            ranking[
                0
            ]
        )

        return {
            "winner": winner,
            "ranking": ranking,
            "ranking_metric": "rmse",
            "results": results,
            "errors": errors,
            "model_objects": (
                model_objects
            )
        }

    # ==========================================
    # ROLLING-ORIGIN BACKTEST DE UN MODELO
    # ==========================================

    def rolling_origin_backtest(
        self,
        dataframe: pd.DataFrame,
        date_column: str,
        target_column: str,
        model_name: str,
        initial_train_size: int | None = None,
        horizon: int = 1,
        step: int = 1,
        max_folds: int | None = 5
    ) -> dict[str, Any]:

        model_name = (
            self._normalize_model_name(
                model_name
            )
        )

        df = self._prepare_dataframe(
            dataframe=dataframe,
            date_column=date_column,
            target_column=target_column
        )

        self._validate_backtest_parameters(
            total_rows=len(
                df
            ),
            initial_train_size=(
                initial_train_size
            ),
            horizon=horizon,
            step=step,
            max_folds=max_folds
        )

        # ==========================================
        # TAMAÑO INICIAL DE TRAIN
        # ==========================================

        resolved_initial_train_size = (
            self._resolve_initial_train_size(
                total_rows=len(
                    df
                ),
                initial_train_size=(
                    initial_train_size
                ),
                horizon=horizon
            )
        )

        feature_columns = (
            []
            if model_name == "arima"
            else self._get_feature_columns(
                df=df,
                date_column=date_column,
                target_column=target_column
            )
        )

        if (
            model_name != "arima"
            and not feature_columns
        ):

            raise ValueError(
                "No existen features "
                "numéricas para realizar "
                f"backtesting de {model_name}"
            )

        # ==========================================
        # GENERAR VENTANAS
        # ==========================================

        windows = (
            self._build_rolling_windows(
                total_rows=len(
                    df
                ),
                initial_train_size=(
                    resolved_initial_train_size
                ),
                horizon=horizon,
                step=step,
                max_folds=max_folds
            )
        )

        if not windows:

            raise ValueError(
                "No fue posible generar "
                "ningún fold de backtesting"
            )

        fold_results = []

        fold_errors = []

        # ==========================================
        # EJECUTAR FOLDS
        # ==========================================

        for (
            fold_number,
            (
                train_end,
                test_start,
                test_end,
            )
        ) in enumerate(
            windows,
            start=1
        ):

            train_df = (
                df
                .iloc[
                    :train_end
                ]
                .copy()
            )

            test_df = (
                df
                .iloc[
                    test_start:test_end
                ]
                .copy()
            )

            try:

                result = (
                    self._evaluate_split(
                        train_df=train_df,
                        test_df=test_df,
                        date_column=date_column,
                        target_column=target_column,
                        model_name=model_name,
                        feature_columns=(
                            feature_columns
                        )
                    )
                )

                evaluation = (
                    result[
                        "evaluation"
                    ]
                )

                fold_result = {
                    "fold": (
                        fold_number
                    ),
                    "training_rows": int(
                        len(
                            train_df
                        )
                    ),
                    "testing_rows": int(
                        len(
                            test_df
                        )
                    ),
                    "train_start_date": (
                        train_df[
                            date_column
                        ]
                        .iloc[
                            0
                        ]
                        .isoformat()
                    ),
                    "train_end_date": (
                        train_df[
                            date_column
                        ]
                        .iloc[
                            -1
                        ]
                        .isoformat()
                    ),
                    "test_start_date": (
                        test_df[
                            date_column
                        ]
                        .iloc[
                            0
                        ]
                        .isoformat()
                    ),
                    "test_end_date": (
                        test_df[
                            date_column
                        ]
                        .iloc[
                            -1
                        ]
                        .isoformat()
                    ),
                    "metrics": (
                        evaluation[
                            "metrics"
                        ]
                    ),
                    "predictions": (
                        evaluation.get(
                            "predictions",
                            []
                        )
                    ),
                    "actual_values": [
                        float(
                            value
                        )
                        for value
                        in test_df[
                            target_column
                        ]
                    ],
                    "test_dates": [
                        value.isoformat()
                        for value
                        in test_df[
                            date_column
                        ]
                    ],
                }

                fold_results.append(
                    fold_result
                )

            except Exception as error:

                fold_errors.append(
                    {
                        "fold": (
                            fold_number
                        ),
                        "training_rows": int(
                            len(
                                train_df
                            )
                        ),
                        "testing_rows": int(
                            len(
                                test_df
                            )
                        ),
                        "error": str(
                            error
                        ),
                    }
                )

        if not fold_results:

            raise RuntimeError(
                f"Ningún fold de {model_name} "
                "pudo evaluarse correctamente"
            )

        # ==========================================
        # AGREGAR MÉTRICAS
        # ==========================================

        aggregate = (
            self._aggregate_fold_metrics(
                fold_results
            )
        )

        return {
            "model": (
                model_name
            ),
            "strategy": (
                "rolling_origin_expanding_window"
            ),
            "total_rows": int(
                len(
                    df
                )
            ),
            "initial_train_size": int(
                resolved_initial_train_size
            ),
            "horizon": int(
                horizon
            ),
            "step": int(
                step
            ),
            "requested_max_folds": (
                max_folds
            ),
            "successful_folds": int(
                len(
                    fold_results
                )
            ),
            "failed_folds": int(
                len(
                    fold_errors
                )
            ),
            "feature_columns": (
                feature_columns
            ),
            "mean_metrics": (
                aggregate[
                    "mean_metrics"
                ]
            ),
            "std_metrics": (
                aggregate[
                    "std_metrics"
                ]
            ),
            "min_metrics": (
                aggregate[
                    "min_metrics"
                ]
            ),
            "max_metrics": (
                aggregate[
                    "max_metrics"
                ]
            ),
            "folds": (
                fold_results
            ),
            "errors": (
                fold_errors
            ),
            "methodological_note": (
                self._backtest_methodological_note(
                    horizon=horizon
                )
            ),
        }

    # ==========================================
    # COMPARAR TODOS CON ROLLING-ORIGIN
    # ==========================================

    def compare_all_backtest(
        self,
        dataframe: pd.DataFrame,
        date_column: str,
        target_column: str,
        initial_train_size: int | None = None,
        horizon: int = 1,
        step: int = 1,
        max_folds: int | None = 5
    ) -> dict[str, Any]:

        results = {}
        errors = {}

        for model_name in [
            "arima",
            "random_forest",
            "xgboost",
            "hybrid",
        ]:

            try:

                results[
                    model_name
                ] = (
                    self
                    .rolling_origin_backtest(
                        dataframe=dataframe,
                        date_column=date_column,
                        target_column=target_column,
                        model_name=model_name,
                        initial_train_size=(
                            initial_train_size
                        ),
                        horizon=horizon,
                        step=step,
                        max_folds=max_folds
                    )
                )

            except Exception as error:

                errors[
                    model_name
                ] = str(
                    error
                )

        if not results:

            raise RuntimeError(
                "Ningún modelo pudo ser "
                "evaluado mediante "
                "rolling-origin backtesting"
            )

        # ==========================================
        # RANKING POR RMSE PROMEDIO
        # ==========================================

        ranking = sorted(
            results.keys(),
            key=lambda name: (
                self._safe_ranking_metric(
                    results[
                        name
                    ][
                        "mean_metrics"
                    ].get(
                        "rmse"
                    )
                )
            )
        )

        winner = (
            ranking[
                0
            ]
        )

        ranking_details = []

        for (
            position,
            model_name
        ) in enumerate(
            ranking,
            start=1
        ):

            model_result = (
                results[
                    model_name
                ]
            )

            ranking_details.append(
                {
                    "position": (
                        position
                    ),
                    "model": (
                        model_name
                    ),
                    "mean_rmse": (
                        model_result[
                            "mean_metrics"
                        ].get(
                            "rmse"
                        )
                    ),
                    "std_rmse": (
                        model_result[
                            "std_metrics"
                        ].get(
                            "rmse"
                        )
                    ),
                    "mean_mae": (
                        model_result[
                            "mean_metrics"
                        ].get(
                            "mae"
                        )
                    ),
                    "mean_mape": (
                        model_result[
                            "mean_metrics"
                        ].get(
                            "mape"
                        )
                    ),
                    "mean_smape": (
                        model_result[
                            "mean_metrics"
                        ].get(
                            "smape"
                        )
                    ),
                    "mean_r2": (
                        model_result[
                            "mean_metrics"
                        ].get(
                            "r2"
                        )
                    ),
                    "successful_folds": (
                        model_result[
                            "successful_folds"
                        ]
                    ),
                }
            )

        return {
            "winner": (
                winner
            ),
            "ranking": (
                ranking
            ),
            "ranking_metric": (
                "mean_rmse"
            ),
            "ranking_details": (
                ranking_details
            ),
            "strategy": (
                "rolling_origin_expanding_window"
            ),
            "horizon": int(
                horizon
            ),
            "step": int(
                step
            ),
            "max_folds": (
                max_folds
            ),
            "results": (
                results
            ),
            "errors": (
                errors
            ),
            "methodological_note": (
                self._backtest_methodological_note(
                    horizon=horizon
                )
            ),
        }

    # ==========================================
    # EVALUAR UN SPLIT
    # ==========================================

    def _evaluate_split(
        self,
        train_df: pd.DataFrame,
        test_df: pd.DataFrame,
        date_column: str,
        target_column: str,
        model_name: str,
        feature_columns: list[str]
    ) -> dict[str, Any]:

        if train_df.empty:

            raise ValueError(
                "El conjunto de entrenamiento "
                "está vacío"
            )

        if test_df.empty:

            raise ValueError(
                "El conjunto de prueba "
                "está vacío"
            )

        y_train = (
            train_df[
                target_column
            ]
        )

        y_test = (
            test_df[
                target_column
            ]
        )

        # ==========================================
        # ARIMA
        # ==========================================

        if model_name == "arima":

            model = (
                ArimaDemandModel()
            )

            evaluation = (
                model.evaluate(
                    train_y=y_train,
                    test_y=y_test
                )
            )

            return {
                "model_object": (
                    model
                ),
                "evaluation": (
                    evaluation
                ),
            }

        # ==========================================
        # ML / HYBRID
        # ==========================================

        if not feature_columns:

            raise ValueError(
                "No existen features "
                "numéricas para entrenar "
                f"{model_name}"
            )

        X_train = (
            train_df[
                feature_columns
            ]
        )

        X_test = (
            test_df[
                feature_columns
            ]
        )

        if model_name == "random_forest":

            model = (
                RandomForestDemandModel()
            )

        elif model_name == "xgboost":

            model = (
                XGBoostDemandModel()
            )

        elif model_name == "hybrid":

            model = (
                HybridDemandModel()
            )

        else:

            raise ValueError(
                "Modelo no soportado: "
                f"{model_name}"
            )

        evaluation = (
            model.evaluate(
                X_train=X_train,
                y_train=y_train,
                X_test=X_test,
                y_test=y_test
            )
        )

        return {
            "model_object": (
                model
            ),
            "evaluation": (
                evaluation
            ),
        }

    # ==========================================
    # AGREGAR MÉTRICAS DE FOLDS
    # ==========================================

    def _aggregate_fold_metrics(
        self,
        folds: list[dict]
    ) -> dict[str, dict]:

        mean_metrics = {}
        std_metrics = {}
        min_metrics = {}
        max_metrics = {}

        for metric_name in (
            self.METRIC_NAMES
        ):

            values = []

            for fold in folds:

                value = (
                    fold[
                        "metrics"
                    ].get(
                        metric_name
                    )
                )

                if value is None:
                    continue

                try:

                    numeric_value = float(
                        value
                    )

                except (
                    TypeError,
                    ValueError,
                ):
                    continue

                if not math.isfinite(
                    numeric_value
                ):
                    continue

                values.append(
                    numeric_value
                )

            if not values:

                mean_metrics[
                    metric_name
                ] = None

                std_metrics[
                    metric_name
                ] = None

                min_metrics[
                    metric_name
                ] = None

                max_metrics[
                    metric_name
                ] = None

                continue

            mean_metrics[
                metric_name
            ] = float(
                mean(
                    values
                )
            )

            std_metrics[
                metric_name
            ] = (
                float(
                    stdev(
                        values
                    )
                )
                if len(
                    values
                ) >= 2
                else 0.0
            )

            min_metrics[
                metric_name
            ] = float(
                min(
                    values
                )
            )

            max_metrics[
                metric_name
            ] = float(
                max(
                    values
                )
            )

        return {
            "mean_metrics": (
                mean_metrics
            ),
            "std_metrics": (
                std_metrics
            ),
            "min_metrics": (
                min_metrics
            ),
            "max_metrics": (
                max_metrics
            ),
        }

    # ==========================================
    # VENTANAS ROLLING ORIGIN
    # ==========================================

    @staticmethod
    def _build_rolling_windows(
        total_rows: int,
        initial_train_size: int,
        horizon: int,
        step: int,
        max_folds: int | None
    ) -> list[
        tuple[
            int,
            int,
            int,
        ]
    ]:

        windows = []

        train_end = (
            initial_train_size
        )

        while (
            train_end
            +
            horizon
            <= total_rows
        ):

            test_start = (
                train_end
            )

            test_end = (
                test_start
                +
                horizon
            )

            windows.append(
                (
                    train_end,
                    test_start,
                    test_end,
                )
            )

            train_end += (
                step
            )

        # ==========================================
        # SI max_folds ESTÁ DEFINIDO,
        # TOMAMOS LOS FOLDS MÁS RECIENTES.
        #
        # Así evaluamos comportamiento próximo
        # al final de la serie.
        # ==========================================

        if (
            max_folds is not None
            and len(
                windows
            )
            > max_folds
        ):

            windows = (
                windows[
                    -max_folds:
                ]
            )

        return windows

    # ==========================================
    # RESOLVER TAMAÑO INICIAL
    # ==========================================

    @staticmethod
    def _resolve_initial_train_size(
        total_rows: int,
        initial_train_size: int | None,
        horizon: int
    ) -> int:

        if initial_train_size is not None:

            return int(
                initial_train_size
            )

        # ==========================================
        # POR DEFECTO:
        # 70 % PARA EL PRIMER TRAIN,
        # PERO NUNCA MENOS DE 30.
        # ==========================================

        proposed = int(
            total_rows
            *
            0.70
        )

        proposed = max(
            30,
            proposed
        )

        maximum_allowed = (
            total_rows
            -
            horizon
        )

        return min(
            proposed,
            maximum_allowed
        )

    # ==========================================
    # VALIDAR BACKTEST
    # ==========================================

    @staticmethod
    def _validate_backtest_parameters(
        total_rows: int,
        initial_train_size: int | None,
        horizon: int,
        step: int,
        max_folds: int | None
    ) -> None:

        if total_rows < 31:

            raise ValueError(
                "Se requieren al menos "
                "31 registros para realizar "
                "rolling-origin backtesting"
            )

        if horizon <= 0:

            raise ValueError(
                "horizon debe ser "
                "mayor que 0"
            )

        if step <= 0:

            raise ValueError(
                "step debe ser "
                "mayor que 0"
            )

        if max_folds is not None:

            if max_folds <= 0:

                raise ValueError(
                    "max_folds debe ser "
                    "mayor que 0"
                )

        if initial_train_size is not None:

            if initial_train_size < 30:

                raise ValueError(
                    "initial_train_size debe "
                    "ser al menos 30"
                )

            if (
                initial_train_size
                +
                horizon
                >
                total_rows
            ):

                raise ValueError(
                    "initial_train_size + "
                    "horizon supera la cantidad "
                    "de registros disponibles"
                )

    # ==========================================
    # NOTA METODOLÓGICA
    # ==========================================

    @staticmethod
    def _backtest_methodological_note(
        horizon: int
    ) -> str:

        if horizon == 1:

            return (
                "Evaluación rolling-origin con "
                "ventana de entrenamiento "
                "expansiva y pronóstico de un "
                "paso hacia adelante. Esta "
                "configuración evita utilizar "
                "valores reales futuros dentro "
                "del mismo horizonte de prueba "
                "para construir lags posteriores."
            )

        return (
            "Evaluación rolling-origin con "
            "ventana expansiva y horizonte "
            f"de {horizon} pasos. Para modelos "
            "que utilizan lags o rolling features "
            "precalculadas, horizon=1 es la "
            "configuración recomendada para "
            "una evaluación estrictamente "
            "one-step-ahead."
        )

    # ==========================================
    # NORMALIZAR MODELO
    # ==========================================

    def _normalize_model_name(
        self,
        model_name: str
    ) -> str:

        normalized = (
            str(
                model_name
            )
            .lower()
            .strip()
        )

        if normalized not in (
            self.SUPPORTED_MODELS
        ):

            raise ValueError(
                "Modelo no soportado: "
                f"{normalized}"
            )

        return normalized

    # ==========================================
    # PREPARAR DATAFRAME
    # ==========================================

    @staticmethod
    def _prepare_dataframe(
        dataframe: pd.DataFrame,
        date_column: str,
        target_column: str
    ) -> pd.DataFrame:

        if dataframe is None:

            raise ValueError(
                "El dataset no puede ser None"
            )

        if dataframe.empty:

            raise ValueError(
                "El dataset está vacío"
            )

        if date_column not in (
            dataframe.columns
        ):

            raise ValueError(
                f"No existe la columna "
                f"fecha: {date_column}"
            )

        if target_column not in (
            dataframe.columns
        ):

            raise ValueError(
                f"No existe la columna "
                f"objetivo: {target_column}"
            )

        df = (
            dataframe.copy()
        )

        df[
            date_column
        ] = pd.to_datetime(
            df[
                date_column
            ],
            errors="coerce"
        )

        df[
            target_column
        ] = pd.to_numeric(
            df[
                target_column
            ],
            errors="coerce"
        )

        df = (
            df
            .dropna(
                subset=[
                    date_column,
                    target_column,
                ]
            )
            .sort_values(
                date_column
            )
            .reset_index(
                drop=True
            )
        )

        if df.empty:

            raise ValueError(
                "No quedaron registros "
                "válidos para entrenar"
            )

        return df

    # ==========================================
    # FEATURES
    # ==========================================

    @staticmethod
    def _get_feature_columns(
        df: pd.DataFrame,
        date_column: str,
        target_column: str
    ) -> list[str]:

        numeric_columns = (
            df
            .select_dtypes(
                include=[
                    "number",
                    "bool",
                ]
            )
            .columns
            .tolist()
        )

        excluded = {
            target_column,
            date_column,
        }

        return [
            column
            for column
            in numeric_columns
            if column not in excluded
        ]

    # ==========================================
    # MÉTRICA SEGURA PARA RANKING
    # ==========================================

    @staticmethod
    def _safe_ranking_metric(
        value
    ) -> float:

        if value is None:

            return float(
                "inf"
            )

        try:

            numeric = float(
                value
            )

        except (
            TypeError,
            ValueError,
        ):

            return float(
                "inf"
            )

        if not np.isfinite(
            numeric
        ):

            return float(
                "inf"
            )

        return numeric