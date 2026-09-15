from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

import numpy as np
import pandas as pd


@dataclass
class ValidationIssue:
    level: str
    code: str
    message: str
    column: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class DatasetValidator:

    DATE_HINTS = {
        "fecha",
        "date",
        "datetime",
        "timestamp",
        "dia",
        "día",
        "day",
        "periodo",
        "period",
    }

    TARGET_HINTS = {
        "demanda",
        "demand",
        "ventas",
        "sales",
        "cantidad",
        "quantity",
        "qty",
        "unidades",
        "units",
        "consumo",
        "consumption",
    }

    def analyze(
        self,
        dataframe: pd.DataFrame
    ) -> dict[str, Any]:

        if dataframe is None:
            return self._empty_result(
                "El dataset es None"
            )

        if dataframe.empty:
            return self._empty_result(
                "El dataset no contiene registros"
            )

        df = dataframe.copy()

        issues: list[ValidationIssue] = []

        date_column = self.detect_date_column(
            df
        )

        target_column = self.detect_target_column(
            df
        )

        duplicates = int(
            df.duplicated().sum()
        )

        if duplicates > 0:
            issues.append(
                ValidationIssue(
                    level="warning",
                    code="duplicate_rows",
                    message=(
                        f"Se detectaron {duplicates} "
                        "filas duplicadas"
                    )
                )
            )

        null_report = (
            self._null_report(
                df
            )
        )

        columns_with_nulls = [
            item
            for item in null_report
            if item["null_count"] > 0
        ]

        if columns_with_nulls:
            issues.append(
                ValidationIssue(
                    level="warning",
                    code="missing_values",
                    message=(
                        "El dataset contiene "
                        "valores nulos"
                    )
                )
            )

        if not date_column:
            issues.append(
                ValidationIssue(
                    level="error",
                    code="date_column_not_detected",
                    message=(
                        "No se pudo detectar "
                        "una columna de fecha"
                    )
                )
            )

        if not target_column:
            issues.append(
                ValidationIssue(
                    level="error",
                    code="target_column_not_detected",
                    message=(
                        "No se pudo detectar "
                        "una columna objetivo "
                        "de demanda o ventas"
                    )
                )
            )

        frequency = None
        date_range = None

        if date_column:
            date_analysis = (
                self._analyze_dates(
                    df,
                    date_column
                )
            )

            frequency = (
                date_analysis[
                    "frequency"
                ]
            )

            date_range = (
                date_analysis[
                    "date_range"
                ]
            )

            issues.extend(
                date_analysis[
                    "issues"
                ]
            )

        target_analysis = None

        if target_column:
            target_analysis = (
                self._analyze_target(
                    df,
                    target_column
                )
            )

            issues.extend(
                target_analysis[
                    "issues"
                ]
            )

        outliers = {}

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
            outliers[column] = (
                self._detect_outliers(
                    df[column]
                )
            )

        errors = [
            issue
            for issue in issues
            if issue.level == "error"
        ]

        warnings = [
            issue
            for issue in issues
            if issue.level == "warning"
        ]

        if errors:
            status = "not_ready"

        elif warnings:
            status = "ready_with_warnings"

        else:
            status = "ready"

        return {
            "status": status,
            "is_trainable": (
                len(errors) == 0
            ),
            "rows": int(
                len(df)
            ),
            "columns": int(
                len(df.columns)
            ),
            "date_column": (
                date_column
            ),
            "target_column": (
                target_column
            ),
            "frequency": frequency,
            "date_range": date_range,
            "duplicate_rows": (
                duplicates
            ),
            "null_report": (
                null_report
            ),
            "numeric_columns": (
                numeric_columns
            ),
            "outliers": (
                outliers
            ),
            "target_analysis": (
                target_analysis
            ),
            "issues": [
                issue.to_dict()
                for issue in issues
            ],
            "summary": {
                "errors": len(
                    errors
                ),
                "warnings": len(
                    warnings
                )
            }
        }

    def detect_date_column(
        self,
        dataframe: pd.DataFrame
    ) -> str | None:

        columns = list(
            dataframe.columns
        )

        for column in columns:

            normalized = (
                str(column)
                .strip()
                .lower()
            )

            if normalized in self.DATE_HINTS:
                return str(
                    column
                )

        for column in columns:

            series = dataframe[
                column
            ]

            if pd.api.types.is_datetime64_any_dtype(
                series
            ):
                return str(
                    column
                )

        for column in columns:

            series = dataframe[
                column
            ]

            if (
                pd.api.types
                .is_object_dtype(
                    series
                )
                or pd.api.types
                .is_string_dtype(
                    series
                )
            ):
                sample = (
                    series
                    .dropna()
                    .head(100)
                )

                if sample.empty:
                    continue

                # dayfirst=True: nuestras fechas son día/mes/año
                # (ej. "02/04/2026" = 2 de abril). Sin esto, pandas
                # asume mes/día/año y para días <=12 malinterpreta
                # la fecha sin avisar.
                parsed = pd.to_datetime(
                    sample,
                    errors="coerce",
                    dayfirst=True
                )

                ratio = float(
                    parsed.notna().mean()
                )

                if ratio >= 0.8:
                    return str(
                        column
                    )

        return None

    def detect_target_column(
        self,
        dataframe: pd.DataFrame
    ) -> str | None:

        columns = list(
            dataframe.columns
        )

        for column in columns:

            normalized = (
                str(column)
                .strip()
                .lower()
            )

            if normalized in self.TARGET_HINTS:
                return str(
                    column
                )

        numeric_columns = (
            dataframe
            .select_dtypes(
                include=[
                    np.number
                ]
            )
            .columns
            .tolist()
        )

        if len(
            numeric_columns
        ) == 1:
            return str(
                numeric_columns[0]
            )

        return None

    def _analyze_dates(
        self,
        dataframe: pd.DataFrame,
        column: str
    ) -> dict[str, Any]:

        issues: list[
            ValidationIssue
        ] = []

        # dayfirst=True: mismo motivo que en detect_date_column.
        # Fechas como "02/04/2026" deben leerse como 2 de abril,
        # no como 4 de febrero.
        parsed = pd.to_datetime(
            dataframe[
                column
            ],
            errors="coerce",
            dayfirst=True
        )

        invalid_count = int(
            parsed.isna().sum()
        )

        if invalid_count > 0:
            issues.append(
                ValidationIssue(
                    level="warning",
                    code="invalid_dates",
                    column=column,
                    message=(
                        f"Se detectaron "
                        f"{invalid_count} fechas "
                        "inválidas o nulas"
                    )
                )
            )

        valid_dates = (
            parsed
            .dropna()
            .sort_values()
        )

        if valid_dates.empty:
            return {
                "frequency": None,
                "date_range": None,
                "issues": [
                    ValidationIssue(
                        level="error",
                        code="no_valid_dates",
                        column=column,
                        message=(
                            "No existen fechas "
                            "válidas en la columna"
                        )
                    )
                ]
            }

        duplicated_dates = int(
            valid_dates.duplicated().sum()
        )

        if duplicated_dates > 0:
            issues.append(
                ValidationIssue(
                    level="warning",
                    code="duplicated_dates",
                    column=column,
                    message=(
                        f"Se detectaron "
                        f"{duplicated_dates} "
                        "fechas duplicadas"
                    )
                )
            )

        frequency = (
            self._infer_frequency(
                valid_dates
            )
        )

        if not frequency:
            issues.append(
                ValidationIssue(
                    level="warning",
                    code="frequency_not_detected",
                    column=column,
                    message=(
                        "No se pudo inferir "
                        "una frecuencia temporal "
                        "regular"
                    )
                )
            )

        date_range = {
            "min": (
                valid_dates.min()
                .isoformat()
            ),
            "max": (
                valid_dates.max()
                .isoformat()
            )
        }

        return {
            "frequency": frequency,
            "date_range": (
                date_range
            ),
            "issues": issues
        }

    def _analyze_target(
        self,
        dataframe: pd.DataFrame,
        column: str
    ) -> dict[str, Any]:

        issues: list[
            ValidationIssue
        ] = []

        series = pd.to_numeric(
            dataframe[column],
            errors="coerce"
        )

        invalid_count = int(
            series.isna().sum()
        )

        if invalid_count > 0:
            issues.append(
                ValidationIssue(
                    level="warning",
                    code="invalid_target_values",
                    column=column,
                    message=(
                        f"Se detectaron "
                        f"{invalid_count} valores "
                        "no numéricos o nulos "
                        "en la variable objetivo"
                    )
                )
            )

        valid = series.dropna()

        if valid.empty:
            issues.append(
                ValidationIssue(
                    level="error",
                    code="target_without_numeric_values",
                    column=column,
                    message=(
                        "La variable objetivo "
                        "no contiene valores "
                        "numéricos válidos"
                    )
                )
            )

            return {
                "count": 0,
                "min": None,
                "max": None,
                "mean": None,
                "median": None,
                "std": None,
                "negative_values": 0,
                "zero_values": 0,
                "issues": issues
            }

        negative_values = int(
            (
                valid < 0
            ).sum()
        )

        if negative_values > 0:
            issues.append(
                ValidationIssue(
                    level="warning",
                    code="negative_target_values",
                    column=column,
                    message=(
                        f"Se detectaron "
                        f"{negative_values} valores "
                        "negativos en la variable "
                        "objetivo"
                    )
                )
            )

        return {
            "count": int(
                valid.count()
            ),
            "min": float(
                valid.min()
            ),
            "max": float(
                valid.max()
            ),
            "mean": float(
                valid.mean()
            ),
            "median": float(
                valid.median()
            ),
            "std": (
                float(
                    valid.std()
                )
                if len(valid) > 1
                else 0.0
            ),
            "negative_values": (
                negative_values
            ),
            "zero_values": int(
                (
                    valid == 0
                ).sum()
            ),
            "issues": issues
        }

    @staticmethod
    def _infer_frequency(
        dates: pd.Series
    ) -> str | None:

        unique_dates = (
            pd.Series(
                dates.unique()
            )
            .sort_values()
        )

        if len(
            unique_dates
        ) < 3:
            return None

        try:
            frequency = pd.infer_freq(
                pd.DatetimeIndex(
                    unique_dates
                )
            )

            return frequency

        except Exception:
            return None

    @staticmethod
    def _null_report(
        dataframe: pd.DataFrame
    ) -> list[dict[str, Any]]:

        total_rows = len(
            dataframe
        )

        result = []

        for column in dataframe.columns:

            null_count = int(
                dataframe[column]
                .isna()
                .sum()
            )

            percentage = (
                (
                    null_count
                    / total_rows
                )
                * 100
                if total_rows
                else 0.0
            )

            result.append(
                {
                    "column": str(
                        column
                    ),
                    "null_count": (
                        null_count
                    ),
                    "null_percentage": round(
                        percentage,
                        2
                    )
                }
            )

        return result

    @staticmethod
    def _detect_outliers(
        series: pd.Series
    ) -> dict[str, Any]:

        numeric = pd.to_numeric(
            series,
            errors="coerce"
        ).dropna()

        if len(
            numeric
        ) < 4:
            return {
                "count": 0,
                "percentage": 0.0,
                "lower_bound": None,
                "upper_bound": None
            }

        q1 = float(
            numeric.quantile(
                0.25
            )
        )

        q3 = float(
            numeric.quantile(
                0.75
            )
        )

        iqr = q3 - q1

        lower_bound = (
            q1
            - 1.5 * iqr
        )

        upper_bound = (
            q3
            + 1.5 * iqr
        )

        mask = (
            (
                numeric
                < lower_bound
            )
            |
            (
                numeric
                > upper_bound
            )
        )

        count = int(
            mask.sum()
        )

        percentage = (
            count
            / len(
                numeric
            )
            * 100
        )

        return {
            "count": count,
            "percentage": round(
                percentage,
                2
            ),
            "lower_bound": float(
                lower_bound
            ),
            "upper_bound": float(
                upper_bound
            )
        }

    @staticmethod
    def _empty_result(
        message: str
    ) -> dict[str, Any]:

        return {
            "status": "not_ready",
            "is_trainable": False,
            "rows": 0,
            "columns": 0,
            "date_column": None,
            "target_column": None,
            "frequency": None,
            "date_range": None,
            "duplicate_rows": 0,
            "null_report": [],
            "numeric_columns": [],
            "outliers": {},
            "target_analysis": None,
            "issues": [
                {
                    "level": "error",
                    "code": "empty_dataset",
                    "message": message,
                    "column": None
                }
            ],
            "summary": {
                "errors": 1,
                "warnings": 0
            }
        }