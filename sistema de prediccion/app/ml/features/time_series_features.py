from __future__ import annotations

from typing import Any

import pandas as pd


class TimeSeriesFeatureEngineer:

    def create_features(
        self,
        dataframe: pd.DataFrame,
        date_column: str,
        target_column: str,
        lags: list[int] | None = None,
        rolling_windows: list[int] | None = None,
        drop_generated_na: bool = True
    ) -> tuple[
        pd.DataFrame,
        dict[str, Any]
    ]:

        if dataframe is None:
            raise ValueError(
                "El DataFrame no puede ser None"
            )

        if dataframe.empty:
            raise ValueError(
                "El DataFrame está vacío"
            )

        if date_column not in dataframe.columns:
            raise ValueError(
                f"No existe la columna fecha: {date_column}"
            )

        if target_column not in dataframe.columns:
            raise ValueError(
                f"No existe la columna objetivo: {target_column}"
            )

        lags = (
            lags
            if lags is not None
            else [
                1,
                7,
                14,
                28
            ]
        )

        rolling_windows = (
            rolling_windows
            if rolling_windows is not None
            else [
                7,
                14,
                28
            ]
        )

        lags = sorted(
            {
                int(value)
                for value in lags
                if int(value) > 0
            }
        )

        rolling_windows = sorted(
            {
                int(value)
                for value in rolling_windows
                if int(value) > 1
            }
        )

        df = dataframe.copy()

        df[date_column] = pd.to_datetime(
            df[date_column],
            errors="coerce"
        )

        df = (
            df
            .dropna(
                subset=[
                    date_column
                ]
            )
            .sort_values(
                date_column
            )
            .reset_index(
                drop=True
            )
        )

        df["year"] = (
            df[date_column]
            .dt.year
        )

        df["month"] = (
            df[date_column]
            .dt.month
        )

        df["day"] = (
            df[date_column]
            .dt.day
        )

        df["day_of_week"] = (
            df[date_column]
            .dt.dayofweek
        )

        df["day_of_year"] = (
            df[date_column]
            .dt.dayofyear
        )

        df["week_of_year"] = (
            df[date_column]
            .dt.isocalendar()
            .week
            .astype(int)
        )

        df["quarter"] = (
            df[date_column]
            .dt.quarter
        )

        df["is_weekend"] = (
            df["day_of_week"]
            .isin(
                [
                    5,
                    6
                ]
            )
            .astype(int)
        )

        generated_columns = [
            "year",
            "month",
            "day",
            "day_of_week",
            "day_of_year",
            "week_of_year",
            "quarter",
            "is_weekend"
        ]

        for lag in lags:

            column_name = (
                f"{target_column}_lag_{lag}"
            )

            df[column_name] = (
                df[target_column]
                .shift(
                    lag
                )
            )

            generated_columns.append(
                column_name
            )

        for window in rolling_windows:

            mean_column = (
                f"{target_column}_rolling_mean_{window}"
            )

            std_column = (
                f"{target_column}_rolling_std_{window}"
            )

            minimum_column = (
                f"{target_column}_rolling_min_{window}"
            )

            maximum_column = (
                f"{target_column}_rolling_max_{window}"
            )

            shifted_target = (
                df[target_column]
                .shift(1)
            )

            df[mean_column] = (
                shifted_target
                .rolling(
                    window=window
                )
                .mean()
            )

            df[std_column] = (
                shifted_target
                .rolling(
                    window=window
                )
                .std()
            )

            df[minimum_column] = (
                shifted_target
                .rolling(
                    window=window
                )
                .min()
            )

            df[maximum_column] = (
                shifted_target
                .rolling(
                    window=window
                )
                .max()
            )

            generated_columns.extend(
                [
                    mean_column,
                    std_column,
                    minimum_column,
                    maximum_column
                ]
            )

        rows_before_drop = len(
            df
        )

        removed_rows = 0

        if drop_generated_na:

            existing_generated_columns = [
                column
                for column in generated_columns
                if column in df.columns
            ]

            df = (
                df
                .dropna(
                    subset=existing_generated_columns
                )
                .reset_index(
                    drop=True
                )
            )

            removed_rows = (
                rows_before_drop
                - len(df)
            )

        if df.empty:
            raise ValueError(
                "No quedaron suficientes registros "
                "después de generar lags y ventanas. "
                "El dataset necesita más historial."
            )

        report = {
            "date_column": date_column,
            "target_column": target_column,
            "lags": lags,
            "rolling_windows": (
                rolling_windows
            ),
            "generated_columns": (
                generated_columns
            ),
            "generated_column_count": len(
                generated_columns
            ),
            "rows_before_features": (
                rows_before_drop
            ),
            "rows_removed_by_features": (
                removed_rows
            ),
            "final_rows": int(
                len(df)
            ),
            "final_columns": int(
                len(df.columns)
            )
        }

        return (
            df,
            report
        )