from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from sklearn.ensemble import (
    RandomForestRegressor
)

from app.ml.core.metrics import (
    RegressionMetrics
)


class RandomForestDemandModel:

    model_name = "random_forest"

    def __init__(
        self,
        n_estimators: int = 300,
        max_depth: int | None = None,
        min_samples_split: int = 2,
        min_samples_leaf: int = 1,
        random_state: int = 42,
        n_jobs: int = -1
    ):
        self.parameters = {
            "n_estimators": n_estimators,
            "max_depth": max_depth,
            "min_samples_split": (
                min_samples_split
            ),
            "min_samples_leaf": (
                min_samples_leaf
            ),
            "random_state": (
                random_state
            ),
            "n_jobs": n_jobs
        }

        self.model = (
            RandomForestRegressor(
                **self.parameters
            )
        )

        self.feature_names: list[str] = []

    def fit(
        self,
        X: pd.DataFrame,
        y
    ) -> "RandomForestDemandModel":

        X_clean = self._prepare_features(
            X
        )

        y_clean = self._prepare_target(
            y
        )

        if len(X_clean) != len(y_clean):
            raise ValueError(
                "X e y deben tener la misma "
                "cantidad de registros"
            )

        self.feature_names = list(
            X_clean.columns
        )

        self.model.fit(
            X_clean,
            y_clean
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
            "parameters": {
                key: value
                for key, value
                in self.parameters.items()
                if key != "n_jobs"
            },
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
                "Random Forest recibió columnas "
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