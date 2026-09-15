from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


class DatasetPreprocessor:

    def preprocess(
        self,
        dataframe: pd.DataFrame,
        date_column: str,
        target_column: str,
        remove_duplicates: bool = True,
        fill_missing_target: bool = True,
        sort_by_date: bool = True
    ) -> tuple[
        pd.DataFrame,
        dict[str, Any]
    ]:

        if dataframe is None:
            raise ValueError(
                "El dataset no puede ser None"
            )

        if dataframe.empty:
            raise ValueError(
                "El dataset está vacío"
            )

        if (
            date_column
            not in dataframe.columns
        ):
            raise ValueError(
                f"No existe la columna "
                f"de fecha: {date_column}"
            )

        if (
            target_column
            not in dataframe.columns
        ):
            raise ValueError(
                f"No existe la columna "
                f"objetivo: {target_column}"
            )

        df = dataframe.copy()

        report: dict[
            str,
            Any
        ] = {
            "initial_rows": int(
                len(df)
            ),
            "initial_columns": int(
                len(df.columns)
            ),
            "removed_duplicates": 0,
            "invalid_dates_removed": 0,
            "target_missing_before": 0,
            "target_missing_after": 0,
            "operations": []
        }

        df.columns = [
            str(column).strip()
            for column
            in df.columns
        ]

        report[
            "operations"
        ].append(
            "normalized_column_names"
        )

        if remove_duplicates:

            before = len(
                df
            )

            df = (
                df
                .drop_duplicates()
                .copy()
            )

            removed = (
                before
                - len(df)
            )

            report[
                "removed_duplicates"
            ] = int(
                removed
            )

            report[
                "operations"
            ].append(
                "removed_duplicate_rows"
            )

        # dayfirst=True: nuestras fechas vienen en formato día/mes/año
        # (ej. "02/04/2026" = 2 de abril de 2026). Sin esto, pandas asume
        # mes/día/año (estilo EEUU) y para días <=12 interpreta mal la
        # fecha SIN lanzar error (ej. "02/04/2026" se leería como 4 de
        # febrero en vez de 2 de abril).
        df[
            date_column
        ] = pd.to_datetime(
            df[
                date_column
            ],
            errors="coerce",
            dayfirst=True
        )

        invalid_dates = int(
            df[
                date_column
            ]
            .isna()
            .sum()
        )

        report[
            "invalid_dates_removed"
        ] = invalid_dates

        if invalid_dates:
            df = (
                df
                .dropna(
                    subset=[
                        date_column
                    ]
                )
                .copy()
            )

        report[
            "operations"
        ].append(
            "converted_date_column"
        )

        df[
            target_column
        ] = pd.to_numeric(
            df[
                target_column
            ],
            errors="coerce"
        )

        target_missing_before = int(
            df[
                target_column
            ]
            .isna()
            .sum()
        )

        report[
            "target_missing_before"
        ] = (
            target_missing_before
        )

        if (
            fill_missing_target
            and target_missing_before
        ):
            df[
                target_column
            ] = (
                df[
                    target_column
                ]
                .interpolate(
                    method="linear",
                    limit_direction="both"
                )
            )

            report[
                "operations"
            ].append(
                "interpolated_target_missing_values"
            )

        target_missing_after = int(
            df[
                target_column
            ]
            .isna()
            .sum()
        )

        report[
            "target_missing_after"
        ] = (
            target_missing_after
        )

        if target_missing_after:
            df = (
                df
                .dropna(
                    subset=[
                        target_column
                    ]
                )
                .copy()
            )

            report[
                "operations"
            ].append(
                "removed_remaining_target_nulls"
            )

        if sort_by_date:

            df = (
                df
                .sort_values(
                    by=date_column
                )
                .reset_index(
                    drop=True
                )
            )

            report[
                "operations"
            ].append(
                "sorted_by_date"
            )

        report[
            "final_rows"
        ] = int(
            len(df)
        )

        report[
            "final_columns"
        ] = int(
            len(
                df.columns
            )
        )

        return (
            df,
            report
        )

    def fill_numeric_missing_values(
        self,
        dataframe: pd.DataFrame
    ) -> pd.DataFrame:

        df = dataframe.copy()

        numeric_columns = (
            df.select_dtypes(
                include=[
                    np.number
                ]
            )
            .columns
            .tolist()
        )

        for column in numeric_columns:

            if (
                df[column]
                .isna()
                .any()
            ):
                median = (
                    df[column]
                    .median()
                )

                df[column] = (
                    df[column]
                    .fillna(
                        median
                    )
                )

        return df

    def fill_categorical_missing_values(
        self,
        dataframe: pd.DataFrame
    ) -> pd.DataFrame:

        df = dataframe.copy()

        categorical_columns = (
            df.select_dtypes(
                include=[
                    "object",
                    "string",
                    "category"
                ]
            )
            .columns
            .tolist()
        )

        for column in categorical_columns:

            if (
                df[column]
                .isna()
                .any()
            ):
                mode = (
                    df[column]
                    .mode(
                        dropna=True
                    )
                )

                fill_value = (
                    mode.iloc[0]
                    if not mode.empty
                    else "unknown"
                )

                df[column] = (
                    df[column]
                    .fillna(
                        fill_value
                    )
                )

        return df