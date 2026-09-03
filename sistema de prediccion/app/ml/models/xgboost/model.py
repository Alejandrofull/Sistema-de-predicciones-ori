from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from xgboost import (
    XGBRegressor
)

from app.ml.core.metrics import (
    RegressionMetrics
)


class XGBoostDemandModel:

    model_name = "xgboost"

    def __init__(
        self,
        n_estimators: int = 500,
        max_depth: int = 6,
        learning_rate: float = 0.05,
        subsample: float = 0.9,
        colsample_bytree: float = 0.9,
        random_state: int = 42,
        objective: str = (
            "reg:squarederror"
        )
    ):
        self.parameters = {
            "n_estimators": (
                n_estimators
            ),
            "max_depth": max_depth,
            "learning_rate": (
                learning_rate
            ),
            "subsample": subsample,
            "colsample_bytree": (
                colsample_bytree
            ),
            "random_state": (
                random_state
            ),
            "objective": (
                objective
            )
        }

        self.model = XGBRegressor(
            **self.parameters
        )

        self.feature_names: list[str] = []

    def fit(
        self,
        X: pd.DataFrame,
        y
    ) -> "XGBoostDemandModel":

        X_clean = self._prepare_features(
            X
        )

        y_clean = self._prepare_target(
            y
        )

        if len(X_clean) != len(y_clean):
            raise ValueError(
                "X e y deben tener "
                "la misma cantidad de registros"
            )

        self.feature_names = list(
            X_clean.columns
        )

        self.model.fit(
            X_clean,
            y_clean,
            verbose=False
        )

        return self

    def predict(
        self,
        X: pd.DataFrame
    ) -> np.ndarray:

        X_clean = self._prepare_features(
            X
        )

        return np.asarray(
            self.model.predict(
                X_clean
            ),
            dtype=float
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

        predictions = self.predict(
            X_test
        )

        metrics = (
            RegressionMetrics
            .calculate(
                y_test,
                predictions
            )
        )

        importances = {
            feature: float(
                importance
            )
            for feature, importance
            in zip(
                self.feature_names,
                self.model.feature_importances_
            )
        }

        importances = dict(
            sorted(
                importances.items(),
                key=lambda item: (
                    item[1]
                ),
                reverse=True
            )
        )

        return {
            "model": self.model_name,
            "parameters": (
                self.parameters
            ),
            "metrics": metrics,
            "feature_importance": (
                importances
            ),
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

        if X.empty:
            raise ValueError(
                "No existen features "
                "para entrenar"
            )

        result = X.copy()

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
                "XGBoost recibió columnas "
                "no numéricas: "
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