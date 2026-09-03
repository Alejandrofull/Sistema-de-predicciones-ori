from __future__ import annotations

import re

from pathlib import Path
from tempfile import NamedTemporaryFile

import joblib
import numpy as np
import pandas as pd

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.integrations.supabase.storage_service import (
    SupabaseStorageService,
)

from app.repositories.business_series_repository import (
    BusinessSeriesRepository,
)

from app.repositories.dataset_repository import (
    DatasetRepository,
)

from app.repositories.external_variable_value_repository import (
    ExternalVariableValueRepository,
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

from app.repositories.prediction_result_repository import (
    PredictionResultRepository,
)

from app.services.import_service import (
    ImportService,
)


class PredictionService:

    SUPPORTED_MODELS = {
        "arima",
        "random_forest",
        "xgboost",
        "hybrid",
    }

    def __init__(self):

        # ==========================================
        # STORAGE
        # ==========================================

        self.model_storage = (
            SupabaseStorageService(
                bucket="models"
            )
        )

        self.dataset_storage = (
            SupabaseStorageService(
                bucket="datasets"
            )
        )

        # ==========================================
        # SERVICES
        # ==========================================

        self.import_service = (
            ImportService()
        )

    # ==========================================
    # EJECUTAR PREDICCIÓN
    # ==========================================

    def run_prediction(
        self,
        db: Session,
        user_id: int,
        horizon: int,
        dataset_id: int | None,
        business_series_id: int | None,
        clip_negative: bool,
        future_features: list[
            dict
        ] | None
    ) -> dict:

        # ==========================================
        # 1. VALIDAR HORIZONTE
        # ==========================================

        if horizon <= 0:

            raise HTTPException(
                status_code=400,
                detail=(
                    "El horizonte debe ser "
                    "mayor que cero"
                )
            )

        if horizon > 365:

            raise HTTPException(
                status_code=400,
                detail=(
                    "El horizonte máximo "
                    "permitido es 365"
                )
            )

        # ==========================================
        # 2. RESOLVER BUSINESS SERIES
        # ==========================================

        business_series = None

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

            if not business_series.is_active:

                raise HTTPException(
                    status_code=400,
                    detail=(
                        "La serie de negocio "
                        "está inactiva"
                    )
                )

        # ==========================================
        # 3. BUSCAR MODELO ACTIVO
        # ==========================================

        if business_series_id is not None:

            active_model = (
                ModelRepository
                .get_active_by_business_series(
                    db=db,
                    business_series_id=(
                        business_series_id
                    )
                )
            )

        else:

            active_model = (
                ModelRepository
                .get_active_global(
                    db
                )
            )

        if not active_model:

            if business_series_id is not None:

                message = (
                    "No existe un modelo activo "
                    "para la serie de negocio "
                    f"{business_series_id}"
                )

            else:

                message = (
                    "No existe un modelo global "
                    "activo. Para predecir una "
                    "serie específica envíe "
                    "business_series_id."
                )

            raise HTTPException(
                status_code=400,
                detail=message
            )

        # ==========================================
        # 4. VALIDAR TIPO DE MODELO
        # ==========================================

        model_type = (
            active_model.model_type
            .strip()
            .lower()
        )

        if (
            model_type
            not in self.SUPPORTED_MODELS
        ):

            raise HTTPException(
                status_code=400,
                detail=(
                    "Tipo de modelo no "
                    f"soportado: {model_type}"
                )
            )

        # ==========================================
        # 5. BUSCAR VERSIÓN ACTIVA
        # ==========================================

        version = (
            ModelVersionRepository
            .get_active_by_model(
                db=db,
                model_id=(
                    active_model.id
                )
            )
        )

        if not version:

            raise HTTPException(
                status_code=400,
                detail=(
                    "El modelo activo no tiene "
                    "una versión activa"
                )
            )

        if not version.artifact_path:

            raise HTTPException(
                status_code=400,
                detail=(
                    "La versión activa no tiene "
                    "artefacto almacenado"
                )
            )

        # ==========================================
        # 6. CONFIGURACIÓN DEL MODELO
        # ==========================================

        feature_config = (
            version.feature_config
            or {}
        )

        date_column = (
            feature_config.get(
                "date_column"
            )
        )

        target_column = (
            feature_config.get(
                "target_column"
            )
        )

        feature_columns = (
            feature_config.get(
                "feature_columns"
            )
            or []
        )

        external_variables = (
            feature_config.get(
                "external_variables"
            )
            or []
        )

        external_feature_columns = (
            feature_config.get(
                "external_feature_columns"
            )
            or []
        )

        if not date_column:

            raise HTTPException(
                status_code=400,
                detail=(
                    "La versión del modelo "
                    "no tiene date_column "
                    "configurado"
                )
            )

        if not target_column:

            raise HTTPException(
                status_code=400,
                detail=(
                    "La versión del modelo "
                    "no tiene target_column "
                    "configurado"
                )
            )

        # ==========================================
        # 7. RESOLVER DATASET
        # ==========================================

        resolved_dataset_id = (
            dataset_id
            or feature_config.get(
                "dataset_id"
            )
        )

        if not resolved_dataset_id:

            raise HTTPException(
                status_code=400,
                detail=(
                    "No se pudo determinar "
                    "el dataset histórico "
                    "del modelo"
                )
            )

        dataset = (
            DatasetRepository.get_by_id(
                db,
                int(
                    resolved_dataset_id
                )
            )
        )

        if not dataset:

            raise HTTPException(
                status_code=404,
                detail=(
                    "Dataset histórico "
                    "no encontrado"
                )
            )

        if dataset.user_id != user_id:

            raise HTTPException(
                status_code=403,
                detail=(
                    "No tiene acceso "
                    "al dataset histórico"
                )
            )

        if not dataset.storage_path:

            raise HTTPException(
                status_code=400,
                detail=(
                    "El dataset histórico "
                    "no tiene archivo asociado"
                )
            )

        if not dataset.file_format:

            raise HTTPException(
                status_code=400,
                detail=(
                    "El dataset histórico "
                    "no tiene formato registrado"
                )
            )

        # ==========================================
        # 8. VALIDAR RELACIÓN CON BUSINESS SERIES
        # ==========================================

        model_series_id = (
            active_model.business_series_id
        )

        dataset_series_id = (
            dataset.business_series_id
        )

        if (
            model_series_id is not None
            and dataset_series_id
            != model_series_id
        ):

            raise HTTPException(
                status_code=400,
                detail=(
                    "El dataset seleccionado "
                    "no pertenece a la misma "
                    "serie de negocio del modelo"
                )
            )

        if (
            business_series_id is not None
            and model_series_id
            != business_series_id
        ):

            raise HTTPException(
                status_code=400,
                detail=(
                    "El modelo activo no pertenece "
                    "a la serie solicitada"
                )
            )

        # ==========================================
        # 9. CARGAR DATASET
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
                    "El dataset histórico "
                    "está vacío"
                )
            )

        if (
            date_column
            not in dataframe.columns
        ):

            raise HTTPException(
                status_code=400,
                detail=(
                    "No existe la columna "
                    f"'{date_column}' "
                    "en el dataset histórico"
                )
            )

        if (
            target_column
            not in dataframe.columns
        ):

            raise HTTPException(
                status_code=400,
                detail=(
                    "No existe la columna "
                    f"'{target_column}' "
                    "en el dataset histórico"
                )
            )

        # ==========================================
        # 10. PREPARAR HISTÓRICO
        # ==========================================

        dataframe[
            date_column
        ] = pd.to_datetime(
            dataframe[
                date_column
            ],
            errors="coerce"
        )

        dataframe[
            target_column
        ] = pd.to_numeric(
            dataframe[
                target_column
            ],
            errors="coerce"
        )

        dataframe = (
            dataframe
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

        if dataframe.empty:

            raise HTTPException(
                status_code=400,
                detail=(
                    "No existen registros "
                    "históricos válidos"
                )
            )

        # ==========================================
        # 11. VALIDAR FUTURE FEATURES
        # ==========================================

        if (
            future_features is not None
            and len(
                future_features
            ) != horizon
        ):

            raise HTTPException(
                status_code=400,
                detail=(
                    "future_features debe "
                    "contener exactamente "
                    f"{horizon} registros"
                )
            )

        # ==========================================
        # 12. GENERAR FECHAS FUTURAS
        # ==========================================

        future_dates = (
            self._build_future_dates(
                dates=(
                    dataframe[
                        date_column
                    ]
                ),
                horizon=horizon
            )
        )

        # ==========================================
        # 13. CARGAR VARIABLES EXTERNAS FUTURAS
        # ==========================================

        automatic_external_features = (
            self._load_future_external_features(
                db=db,
                external_variables=(
                    external_variables
                ),
                external_feature_columns=(
                    external_feature_columns
                ),
                future_dates=(
                    future_dates
                ),
                business_series=(
                    business_series
                )
            )
        )

        # ==========================================
        # 14. CARGAR ARTEFACTO DEL MODELO
        # ==========================================

        model_object = (
            self._load_model(
                version.artifact_path
            )
        )

        # ==========================================
        # 15. GENERAR PREDICCIÓN
        # ==========================================

        try:

            if model_type == "arima":

                predicted_values = (
                    self._predict_arima(
                        model_object=(
                            model_object
                        ),
                        horizon=horizon
                    )
                )

            elif model_type in {
                "random_forest",
                "xgboost",
            }:

                predicted_values = (
                    self._predict_recursive_ml(
                        model_object=(
                            model_object
                        ),
                        dataframe=(
                            dataframe
                        ),
                        date_column=(
                            date_column
                        ),
                        target_column=(
                            target_column
                        ),
                        feature_columns=(
                            feature_columns
                        ),
                        future_dates=(
                            future_dates
                        ),
                        future_features=(
                            future_features
                        ),
                        automatic_external_features=(
                            automatic_external_features
                        )
                    )
                )

            elif model_type == "hybrid":

                predicted_values = (
                    self._predict_hybrid(
                        model_object=(
                            model_object
                        ),
                        dataframe=(
                            dataframe
                        ),
                        date_column=(
                            date_column
                        ),
                        target_column=(
                            target_column
                        ),
                        feature_columns=(
                            feature_columns
                        ),
                        future_dates=(
                            future_dates
                        ),
                        future_features=(
                            future_features
                        ),
                        automatic_external_features=(
                            automatic_external_features
                        )
                    )
                )

            else:

                raise ValueError(
                    "Tipo de modelo no "
                    f"soportado: {model_type}"
                )

        except HTTPException:
            raise

        except Exception as error:

            raise HTTPException(
                status_code=500,
                detail=(
                    "Error generando "
                    "la predicción: "
                    f"{error}"
                )
            )

        # ==========================================
        # 16. NORMALIZAR VALORES
        # ==========================================

        normalized_predictions = []

        for value in predicted_values:

            numeric_value = float(
                value
            )

            if not np.isfinite(
                numeric_value
            ):

                raise HTTPException(
                    status_code=500,
                    detail=(
                        "El modelo generó "
                        "una predicción inválida"
                    )
                )

            if clip_negative:

                numeric_value = max(
                    0.0,
                    numeric_value
                )

            normalized_predictions.append(
                numeric_value
            )

        predicted_values = (
            normalized_predictions
        )

        # ==========================================
        # 17. CREAR CABECERA DE PREDICCIÓN
        # ==========================================

        resolved_series_id = (
            active_model.business_series_id
        )

        prediction = (
            PredictionRepository.create(
                db=db,
                user_id=user_id,
                model_id=(
                    active_model.id
                ),
                model_version_id=(
                    version.id
                ),
                dataset_id=(
                    dataset.id
                ),
                business_series_id=(
                    resolved_series_id
                ),
                horizon=horizon,
                start_date=(
                    future_dates[
                        0
                    ].date()
                ),
                end_date=(
                    future_dates[
                        -1
                    ].date()
                ),
                status="running"
            )
        )

        # ==========================================
        # 18. GUARDAR RESULTADOS
        # ==========================================

        try:

            result_values = []

            for (
                prediction_date,
                predicted_value
            ) in zip(
                future_dates,
                predicted_values
            ):

                result_values.append(
                    {
                        "prediction_date": (
                            prediction_date.date()
                        ),
                        "predicted_value": (
                            float(
                                predicted_value
                            )
                        ),
                        "actual_value": None,
                        "lower_bound": None,
                        "upper_bound": None,
                    }
                )

            results = (
                PredictionResultRepository
                .create_many(
                    db=db,
                    prediction_id=(
                        prediction.id
                    ),
                    values=(
                        result_values
                    )
                )
            )

            prediction = (
                PredictionRepository
                .mark_completed(
                    db=db,
                    prediction=(
                        prediction
                    )
                )
            )

        except Exception as error:

            try:

                PredictionRepository.mark_failed(
                    db=db,
                    prediction=(
                        prediction
                    )
                )

            except Exception:
                pass

            raise HTTPException(
                status_code=500,
                detail=(
                    "La predicción fue generada, "
                    "pero ocurrió un error "
                    "guardando sus resultados: "
                    f"{error}"
                )
            )

        # ==========================================
        # 19. RESPUESTA
        # ==========================================

        return {
            "prediction": (
                prediction
            ),
            "model_type": (
                active_model.model_type
            ),
            "model_version": (
                version.version_number
            ),
            "results": (
                results
            )
        }

    # ==========================================
    # CARGAR MODELO
    # ==========================================

    def _load_model(
        self,
        artifact_path: str
    ):

        try:

            model_bytes = (
                self.model_storage
                .download_bytes(
                    artifact_path
                )
            )

        except Exception as error:

            raise HTTPException(
                status_code=500,
                detail=(
                    "No se pudo descargar "
                    "el modelo desde Storage: "
                    f"{error}"
                )
            )

        temp_path = None

        try:

            with NamedTemporaryFile(
                delete=False,
                suffix=".joblib"
            ) as tmp:

                tmp.write(
                    model_bytes
                )

                temp_path = Path(
                    tmp.name
                )

            return joblib.load(
                temp_path
            )

        finally:

            if temp_path:

                temp_path.unlink(
                    missing_ok=True
                )

    # ==========================================
    # CARGAR DATASET
    # ==========================================

    def _load_dataset(
        self,
        storage_path: str,
        file_format: str
    ) -> pd.DataFrame:

        try:

            dataset_bytes = (
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

        normalized_format = (
            file_format
            .strip()
            .lower()
            .lstrip(".")
        )

        temp_path = None

        try:

            with NamedTemporaryFile(
                delete=False,
                suffix=(
                    f".{normalized_format}"
                )
            ) as tmp:

                tmp.write(
                    dataset_bytes
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
    # ARIMA
    # ==========================================

    @staticmethod
    def _predict_arima(
        model_object,
        horizon: int
    ) -> list[float]:

        predictions = (
            model_object.predict(
                horizon
            )
        )

        return [
            float(
                value
            )
            for value
            in predictions
        ]

    # ==========================================
    # RANDOM FOREST / XGBOOST RECURSIVO
    # ==========================================

    def _predict_recursive_ml(
        self,
        model_object,
        dataframe: pd.DataFrame,
        date_column: str,
        target_column: str,
        feature_columns: list[str],
        future_dates: pd.DatetimeIndex,
        future_features: list[
            dict
        ] | None,
        automatic_external_features: list[
            dict
        ]
    ) -> list[float]:

        if not feature_columns:

            raise ValueError(
                "El modelo no tiene "
                "feature_columns configuradas"
            )

        history = (
            dataframe[
                [
                    date_column,
                    target_column,
                ]
            ]
            .copy()
        )

        predictions = []

        for (
            index,
            future_date
        ) in enumerate(
            future_dates
        ):

            # ======================================
            # FEATURES AUTOMÁTICAS EXTERNAS
            # ======================================

            automatic_features = (
                automatic_external_features[
                    index
                ]
                if (
                    index
                    <
                    len(
                        automatic_external_features
                    )
                )
                else {}
            )

            # ======================================
            # FEATURES MANUALES / ESCENARIO
            # ======================================

            manual_features = (
                future_features[
                    index
                ]
                if future_features
                else {}
            )

            # ======================================
            # MERGE
            #
            # manual_features tiene prioridad.
            # ======================================

            extra_features = {
                **automatic_features,
                **manual_features,
            }

            # ======================================
            # CONSTRUIR FILA FUTURA
            # ======================================

            feature_row = (
                self._create_feature_row(
                    history=(
                        history
                    ),
                    target_column=(
                        target_column
                    ),
                    feature_columns=(
                        feature_columns
                    ),
                    future_date=(
                        future_date
                    ),
                    extra_features=(
                        extra_features
                    )
                )
            )

            X_future = pd.DataFrame(
                [
                    feature_row
                ],
                columns=(
                    feature_columns
                )
            )

            # ======================================
            # PREDICCIÓN
            # ======================================

            predicted_array = (
                model_object.predict(
                    X_future
                )
            )

            predicted_value = float(
                predicted_array[
                    0
                ]
            )

            if not np.isfinite(
                predicted_value
            ):

                raise ValueError(
                    "El modelo generó "
                    "un valor no finito"
                )

            predictions.append(
                predicted_value
            )

            # ======================================
            # AGREGAR PREDICCIÓN AL HISTORIAL
            # ======================================

            history.loc[
                len(
                    history
                )
            ] = {
                date_column: (
                    future_date
                ),
                target_column: (
                    predicted_value
                ),
            }

        return predictions

    # ==========================================
    # MODELO HÍBRIDO
    # ==========================================

    def _predict_hybrid(
        self,
        model_object,
        dataframe: pd.DataFrame,
        date_column: str,
        target_column: str,
        feature_columns: list[str],
        future_dates: pd.DatetimeIndex,
        future_features: list[
            dict
        ] | None,
        automatic_external_features: list[
            dict
        ]
    ) -> list[float]:

        if not hasattr(
            model_object,
            "arima_result"
        ):

            raise ValueError(
                "El artefacto híbrido "
                "no contiene arima_result"
            )

        if not hasattr(
            model_object,
            "residual_model"
        ):

            raise ValueError(
                "El artefacto híbrido "
                "no contiene residual_model"
            )

        if not feature_columns:

            raise ValueError(
                "El modelo híbrido no tiene "
                "feature_columns configuradas"
            )

        # ==========================================
        # FORECAST BASE ARIMA
        # ==========================================

        arima_predictions = np.asarray(
            model_object
            .arima_result
            .forecast(
                steps=len(
                    future_dates
                )
            ),
            dtype=float
        )

        # ==========================================
        # HISTORIAL RECURSIVO
        # ==========================================

        history = (
            dataframe[
                [
                    date_column,
                    target_column,
                ]
            ]
            .copy()
        )

        predictions = []

        for (
            index,
            future_date
        ) in enumerate(
            future_dates
        ):

            automatic_features = (
                automatic_external_features[
                    index
                ]
                if (
                    index
                    <
                    len(
                        automatic_external_features
                    )
                )
                else {}
            )

            manual_features = (
                future_features[
                    index
                ]
                if future_features
                else {}
            )

            extra_features = {
                **automatic_features,
                **manual_features,
            }

            feature_row = (
                self._create_feature_row(
                    history=(
                        history
                    ),
                    target_column=(
                        target_column
                    ),
                    feature_columns=(
                        feature_columns
                    ),
                    future_date=(
                        future_date
                    ),
                    extra_features=(
                        extra_features
                    )
                )
            )

            X_future = pd.DataFrame(
                [
                    feature_row
                ],
                columns=(
                    feature_columns
                )
            )

            # ======================================
            # CORRECCIÓN XGBOOST
            # ======================================

            residual_prediction = float(
                model_object
                .residual_model
                .predict(
                    X_future
                )[
                    0
                ]
            )

            # ======================================
            # ARIMA + RESIDUO
            # ======================================

            predicted_value = float(
                arima_predictions[
                    index
                ]
                +
                residual_prediction
            )

            if not np.isfinite(
                predicted_value
            ):

                raise ValueError(
                    "El modelo híbrido generó "
                    "un valor no finito"
                )

            predictions.append(
                predicted_value
            )

            # ======================================
            # ACTUALIZAR HISTORIAL
            # ======================================

            history.loc[
                len(
                    history
                )
            ] = {
                date_column: (
                    future_date
                ),
                target_column: (
                    predicted_value
                ),
            }

        return predictions

    # ==========================================
    # CREAR FEATURES FUTURAS
    # ==========================================

    def _create_feature_row(
        self,
        history: pd.DataFrame,
        target_column: str,
        feature_columns: list[str],
        future_date: pd.Timestamp,
        extra_features: dict
    ) -> dict:

        row = {}

        target_history = (
            pd.to_numeric(
                history[
                    target_column
                ],
                errors="coerce"
            )
            .replace(
                [
                    np.inf,
                    -np.inf,
                ],
                np.nan
            )
            .dropna()
            .astype(
                float
            )
        )

        if target_history.empty:

            raise ValueError(
                "El histórico de la variable "
                "objetivo está vacío"
            )

        for feature in feature_columns:

            # ======================================
            # FEATURES DE CALENDARIO
            # ======================================

            if feature == "year":

                value = (
                    future_date.year
                )

            elif feature == "month":

                value = (
                    future_date.month
                )

            elif feature == "day":

                value = (
                    future_date.day
                )

            elif feature == "day_of_week":

                value = (
                    future_date.dayofweek
                )

            elif feature == "day_of_year":

                value = (
                    future_date.dayofyear
                )

            elif feature == "week_of_year":

                value = int(
                    future_date
                    .isocalendar()
                    .week
                )

            elif feature == "quarter":

                value = (
                    future_date.quarter
                )

            elif feature == "is_weekend":

                value = int(
                    future_date.dayofweek
                    in {
                        5,
                        6,
                    }
                )

            # ======================================
            # LAGS
            # ======================================

            else:

                lag = (
                    self._extract_lag(
                        feature=feature,
                        target_column=(
                            target_column
                        )
                    )
                )

                if lag is not None:

                    if (
                        len(
                            target_history
                        )
                        < lag
                    ):

                        raise ValueError(
                            "No existe suficiente "
                            "historial para calcular "
                            f"'{feature}'. "
                            f"Se necesitan al menos "
                            f"{lag} observaciones."
                        )

                    value = float(
                        target_history.iloc[
                            -lag
                        ]
                    )

                else:

                    # ==================================
                    # ROLLING
                    # ==================================

                    rolling = (
                        self._extract_rolling(
                            feature=feature,
                            target_column=(
                                target_column
                            )
                        )
                    )

                    if rolling:

                        (
                            operation,
                            window
                        ) = rolling

                        if (
                            len(
                                target_history
                            )
                            < window
                        ):

                            raise ValueError(
                                "No existe suficiente "
                                "historial para calcular "
                                f"'{feature}'. "
                                f"Se necesitan al menos "
                                f"{window} observaciones."
                            )

                        values = (
                            target_history
                            .iloc[
                                -window:
                            ]
                        )

                        if operation == "mean":

                            value = float(
                                values.mean()
                            )

                        elif operation == "std":

                            value = float(
                                values.std(
                                    ddof=1
                                )
                            )

                            if not np.isfinite(
                                value
                            ):

                                value = 0.0

                        elif operation == "min":

                            value = float(
                                values.min()
                            )

                        elif operation == "max":

                            value = float(
                                values.max()
                            )

                        else:

                            raise ValueError(
                                "Operación rolling "
                                "no soportada: "
                                f"{operation}"
                            )

                    # ==================================
                    # FEATURES EXTERNAS U OTRAS
                    # ==================================

                    elif feature in extra_features:

                        value = (
                            extra_features[
                                feature
                            ]
                        )

                    else:

                        raise ValueError(
                            "La feature "
                            f"'{feature}' no puede "
                            "generarse automáticamente "
                            "y no existe un valor "
                            "externo para la fecha "
                            f"{future_date.date()}. "
                            "Envíela mediante "
                            "future_features o registre "
                            "su valor en "
                            "external_variable_values."
                        )

            # ======================================
            # VALIDAR FEATURE
            # ======================================

            if value is None:

                raise ValueError(
                    "La feature "
                    f"'{feature}' "
                    "no tiene valor"
                )

            try:

                numeric_value = float(
                    value
                )

            except (
                TypeError,
                ValueError,
            ):

                raise ValueError(
                    "La feature "
                    f"'{feature}' debe ser numérica. "
                    f"Valor recibido: {value}"
                )

            if not np.isfinite(
                numeric_value
            ):

                raise ValueError(
                    "La feature "
                    f"'{feature}' contiene "
                    "un valor no finito"
                )

            row[
                feature
            ] = numeric_value

        return row

    # ==========================================
    # VARIABLES EXTERNAS FUTURAS
    # ==========================================

    def _load_future_external_features(
        self,
        db: Session,
        external_variables: list,
        external_feature_columns: list[str],
        future_dates: pd.DatetimeIndex,
        business_series
    ) -> list[dict]:

        # ==========================================
        # BASE
        # ==========================================

        future_values = [
            {}
            for _ in future_dates
        ]

        if not external_feature_columns:

            return future_values

        if not external_variables:

            return future_values

        if len(future_dates) == 0:

            return future_values

        # ==========================================
        # BUSINESS KEY ACTUAL
        # ==========================================

        current_business_key = None

        if business_series is not None:

            current_business_key = (
                business_series
                .external_entity_id
            )

        start_datetime = (
            pd.Timestamp(
                future_dates[
                    0
                ]
            )
            .normalize()
            .to_pydatetime()
        )

        # Incluimos todo el último día.
        end_datetime = (
            pd.Timestamp(
                future_dates[
                    -1
                ]
            )
            .normalize()
            +
            pd.Timedelta(
                days=1
            )
            -
            pd.Timedelta(
                microseconds=1
            )
        ).to_pydatetime()

        feature_set = set(
            external_feature_columns
        )

        # ==========================================
        # RECORRER VARIABLES DEL MODELO
        # ==========================================

        for variable_config in (
            external_variables
        ):

            if not isinstance(
                variable_config,
                dict
            ):
                continue

            variable_id = (
                variable_config.get(
                    "variable_id"
                )
            )

            feature_name = (
                variable_config.get(
                    "feature_name"
                )
            )

            if not variable_id:
                continue

            if not feature_name:
                continue

            if (
                feature_name
                not in feature_set
            ):
                continue

            variable_type = (
                str(
                    variable_config.get(
                        "variable_type",
                        ""
                    )
                )
                .strip()
                .lower()
            )

            # Por ahora solo variables numéricas
            # y booleanas son features ML.
            if (
                variable_type
                not in {
                    "numeric",
                    "boolean",
                }
            ):
                continue

            configured_business_key = (
                variable_config.get(
                    "business_key"
                )
            )

            business_key = (
                current_business_key
                or configured_business_key
            )

            # ======================================
            # CONSULTAR VALORES
            # ======================================

            values = (
                ExternalVariableValueRepository
                .get_by_variable(
                    db=db,
                    variable_id=int(
                        variable_id
                    ),
                    start_date=(
                        start_datetime
                    ),
                    end_date=(
                        end_datetime
                    ),
                    business_key=(
                        business_key
                    ),
                    include_global=True
                )
            )

            # ======================================
            # INDEXAR POR FECHA
            # ======================================

            date_map = (
                self._select_external_values_by_date(
                    values=values,
                    business_key=(
                        business_key
                    )
                )
            )

            # ======================================
            # ASIGNAR A CADA DÍA FUTURO
            # ======================================

            for (
                index,
                future_date
            ) in enumerate(
                future_dates
            ):

                normalized_date = (
                    pd.Timestamp(
                        future_date
                    )
                    .normalize()
                )

                external_value = (
                    date_map.get(
                        normalized_date
                    )
                )

                if external_value is None:

                    continue

                numeric_value = (
                    external_value.numeric_value
                )

                if numeric_value is None:

                    continue

                future_values[
                    index
                ][
                    feature_name
                ] = float(
                    numeric_value
                )

        return future_values

    # ==========================================
    # PRIORIZAR VALOR ESPECÍFICO SOBRE GLOBAL
    # ==========================================

    @staticmethod
    def _select_external_values_by_date(
        values: list,
        business_key: str | None
    ) -> dict:

        selected = {}

        priority_map = {}

        for value in values:

            reference_date = (
                pd.Timestamp(
                    value.reference_date
                )
                .normalize()
            )

            # ======================================
            # PRIORIDAD
            #
            # 2 = específico de la serie
            # 1 = global
            # 0 = otro
            # ======================================

            if (
                business_key is not None
                and value.business_key
                == business_key
            ):

                priority = 2

            elif value.business_key is None:

                priority = 1

            else:

                priority = 0

            current_priority = (
                priority_map.get(
                    reference_date,
                    -1
                )
            )

            # Si tienen la misma prioridad,
            # el registro con mayor ID gana.
            replace = False

            if priority > current_priority:

                replace = True

            elif (
                priority
                == current_priority
                and reference_date
                in selected
            ):

                current_item = (
                    selected[
                        reference_date
                    ]
                )

                if (
                    value.id
                    >
                    current_item.id
                ):

                    replace = True

            elif (
                reference_date
                not in selected
            ):

                replace = True

            if replace:

                selected[
                    reference_date
                ] = value

                priority_map[
                    reference_date
                ] = priority

        return selected

    # ==========================================
    # EXTRAER LAG
    # ==========================================

    @staticmethod
    def _extract_lag(
        feature: str,
        target_column: str
    ) -> int | None:

        pattern = (
            rf"^{re.escape(target_column)}"
            r"_lag_(\d+)$"
        )

        match = re.match(
            pattern,
            feature
        )

        if not match:

            return None

        lag = int(
            match.group(
                1
            )
        )

        if lag <= 0:

            return None

        return lag

    # ==========================================
    # EXTRAER ROLLING
    # ==========================================

    @staticmethod
    def _extract_rolling(
        feature: str,
        target_column: str
    ) -> tuple[
        str,
        int
    ] | None:

        pattern = (
            rf"^{re.escape(target_column)}"
            r"_rolling_"
            r"(mean|std|min|max)"
            r"_(\d+)$"
        )

        match = re.match(
            pattern,
            feature
        )

        if not match:

            return None

        operation = (
            match.group(
                1
            )
        )

        window = int(
            match.group(
                2
            )
        )

        if window <= 0:

            return None

        return (
            operation,
            window
        )

    # ==========================================
    # GENERAR FECHAS FUTURAS
    # ==========================================

    @staticmethod
    def _build_future_dates(
        dates: pd.Series,
        horizon: int
    ) -> pd.DatetimeIndex:

        clean_dates = (
            pd.to_datetime(
                dates,
                errors="coerce"
            )
            .dropna()
            .drop_duplicates()
            .sort_values()
        )

        if clean_dates.empty:

            raise ValueError(
                "No existen fechas válidas "
                "para construir el horizonte"
            )

        last_date = (
            clean_dates.iloc[
                -1
            ]
        )

        # ==========================================
        # INTENTAR INFERIR FRECUENCIA
        # ==========================================

        inferred_frequency = None

        if len(clean_dates) >= 3:

            try:

                inferred_frequency = (
                    pd.infer_freq(
                        pd.DatetimeIndex(
                            clean_dates
                        )
                    )
                )

            except Exception:

                inferred_frequency = None

        if inferred_frequency:

            offset = (
                pd.tseries
                .frequencies
                .to_offset(
                    inferred_frequency
                )
            )

            return pd.date_range(
                start=(
                    last_date
                    +
                    offset
                ),
                periods=horizon,
                freq=(
                    inferred_frequency
                )
            )

        # ==========================================
        # FALLBACK POR MEDIANA DE INTERVALOS
        # ==========================================

        if len(clean_dates) >= 2:

            differences = (
                clean_dates
                .diff()
                .dropna()
            )

            median_difference = (
                differences.median()
            )

            if (
                median_difference
                <= pd.Timedelta(
                    hours=36
                )
            ):

                frequency = "D"

            elif (
                median_difference
                <= pd.Timedelta(
                    days=8
                )
            ):

                frequency = "W"

            elif (
                median_difference
                <= pd.Timedelta(
                    days=32
                )
            ):

                frequency = "MS"

            else:

                frequency = "D"

        else:

            frequency = "D"

        offset = (
            pd.tseries
            .frequencies
            .to_offset(
                frequency
            )
        )

        return pd.date_range(
            start=(
                last_date
                +
                offset
            ),
            periods=horizon,
            freq=(
                frequency
            )
        )