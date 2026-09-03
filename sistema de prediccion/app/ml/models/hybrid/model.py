from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from statsmodels.tsa.arima.model import (
    ARIMA
)

from xgboost import (
    XGBRegressor
)

from app.ml.core.metrics import (
    RegressionMetrics
)


class HybridDemandModel:

    model_name = "hybrid"

    def __init__(
        self,
        arima_order: tuple[
            int,
            int,
            int
        ] = (
            5,
            1,
            1
        ),
        xgb_parameters: dict[
            str,
            Any
        ] | None = None
    ):
        self.arima_order = (
            arima_order
        )

        self.xgb_parameters = (
            xgb_parameters
            or {
                "n_estimators": 400,
                "max_depth": 5,
                "learning_rate": 0.05,
                "subsample": 0.9,
                "colsample_bytree": 0.9,
                "random_state": 42,
                "objective": (
                    "reg:squarederror"
                )
            }
        )

        self.arima_result = None

        self.residual_model = (
            XGBRegressor(
                **self.xgb_parameters
            )
        )

        self.feature_names: list[
            str
        ] = []

    def fit(
        self,
        X: pd.DataFrame,
        y
    ) -> "HybridDemandModel":

        X_clean = (
            self._prepare_features(
                X
            )
        )

        y_clean = (
            self._prepare_target(
                y
            )
        )

        if len(X_clean) != len(
            y_clean
        ):
            raise ValueError(
                "X e y deben tener la "
                "misma cantidad de registros"
            )

        if len(y_clean) < 15:
            raise ValueError(
                "El modelo híbrido necesita "
                "al menos 15 observaciones"
            )

        arima = ARIMA(
            y_clean,
            order=self.arima_order
        )

        self.arima_result = (
            arima.fit()
        )

        fitted_values = np.asarray(
            self.arima_result
            .fittedvalues,
            dtype=float
        )

        residuals = (
            y_clean
            -
            fitted_values
        )

        valid_mask = (
            np.isfinite(
                residuals
            )
        )

        X_residual = (
            X_clean
            .iloc[
                np.where(
                    valid_mask
                )[0]
            ]
        )

        residual_target = (
            residuals[
                valid_mask
            ]
        )

        self.feature_names = list(
            X_clean.columns
        )

        self.residual_model.fit(
            X_residual,
            residual_target,
            verbose=False
        )

        return self

    def predict_test(
        self,
        X_test: pd.DataFrame,
        steps: int
    ) -> np.ndarray:

        if self.arima_result is None:
            raise RuntimeError(
                "El modelo híbrido "
                "no ha sido entrenado"
            )

        X_clean = (
            self._prepare_features(
                X_test
            )
        )

        arima_forecast = (
            np.asarray(
                self.arima_result
                .forecast(
                    steps=steps
                ),
                dtype=float
            )
        )

        residual_forecast = (
            np.asarray(
                self.residual_model
                .predict(
                    X_clean
                ),
                dtype=float
            )
        )

        if len(
            residual_forecast
        ) != len(
            arima_forecast
        ):
            raise RuntimeError(
                "Las predicciones ARIMA y "
                "XGBoost tienen tamaños diferentes"
            )

        return (
            arima_forecast
            +
            residual_forecast
        )

    def evaluate(
        self,
        X_train: pd.DataFrame,
        y_train,
        X_test: pd.DataFrame,
        y_test
    ) -> dict[str, Any]:

        self.fit(
            X_train,
            y_train
        )

        predictions = (
            self.predict_test(
                X_test=X_test,
                steps=len(
                    y_test
                )
            )
        )

        metrics = (
            RegressionMetrics
            .calculate(
                y_test,
                predictions
            )
        )

        return {
            "model": self.model_name,
            "parameters": {
                "arima_order": list(
                    self.arima_order
                ),
                "xgboost": (
                    self.xgb_parameters
                )
            },
            "metrics": metrics,
            "predictions": (
                predictions.tolist()
            )
        }

    @staticmethod
    def _prepare_features(
        X: pd.DataFrame
    ) -> pd.DataFrame:

        if not isinstance(
            X,
            pd.DataFrame
        ):
            X = pd.DataFrame(
                X
            )

        result = X.copy()

        if result.empty:
            raise ValueError(
                "No existen features "
                "para el modelo híbrido"
            )

        non_numeric = (
            result
            .select_dtypes(
                exclude=[
                    "number",
                    "bool"
                ]
            )
            .columns
            .tolist()
        )

        if non_numeric:
            raise ValueError(
                "El modelo híbrido recibió "
                "columnas no numéricas: "
                + ", ".join(
                    map(
                        str,
                        non_numeric
                    )
                )
            )

        result = (
            result
            .replace(
                [
                    np.inf,
                    -np.inf
                ],
                np.nan
            )
        )

        for column in result.columns:

            if result[
                column
            ].isna().any():

                median = (
                    result[
                        column
                    ]
                    .median()
                )

                result[
                    column
                ] = (
                    result[
                        column
                    ]
                    .fillna(
                        median
                    )
                )

        return result.astype(
            float
        )

    @staticmethod
    def _prepare_target(
        y
    ) -> np.ndarray:

        values = pd.to_numeric(
            pd.Series(
                y
            ),
            errors="coerce"
        )

        if values.isna().any():
            raise ValueError(
                "La variable objetivo contiene "
                "valores inválidos"
            )

        return values.to_numpy(
            dtype=float
        )