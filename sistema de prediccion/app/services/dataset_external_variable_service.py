from __future__ import annotations

import re
import unicodedata

import pandas as pd

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories.business_series_repository import (
    BusinessSeriesRepository,
)

from app.repositories.dataset_external_variable_repository import (
    DatasetExternalVariableRepository,
)

from app.repositories.dataset_repository import (
    DatasetRepository,
)

from app.repositories.external_variable_repository import (
    ExternalVariableRepository,
)

from app.repositories.external_variable_value_repository import (
    ExternalVariableValueRepository,
)


class DatasetExternalVariableService:

    SUPPORTED_ML_TYPES = {
        "numeric",
        "boolean",
    }

    @staticmethod
    def attach_variable(
        db: Session,
        dataset_id: int,
        variable_id: int,
        user_id: int
    ):

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

        variable = (
            ExternalVariableRepository
            .get_by_id(
                db,
                variable_id
            )
        )

        if not variable:

            raise HTTPException(
                status_code=404,
                detail=(
                    "Variable externa "
                    "no encontrada"
                )
            )

        if not variable.is_active:

            raise HTTPException(
                status_code=400,
                detail=(
                    "La variable externa "
                    "está inactiva"
                )
            )

        return (
            DatasetExternalVariableRepository
            .attach(
                db=db,
                dataset_id=dataset.id,
                external_variable_id=(
                    variable.id
                )
            )
        )

    @staticmethod
    def detach_variable(
        db: Session,
        dataset_id: int,
        variable_id: int,
        user_id: int
    ) -> None:

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

        link = (
            DatasetExternalVariableRepository
            .get_link(
                db=db,
                dataset_id=dataset.id,
                external_variable_id=(
                    variable_id
                )
            )
        )

        if not link:

            raise HTTPException(
                status_code=404,
                detail=(
                    "La variable externa "
                    "no está asociada "
                    "al dataset"
                )
            )

        DatasetExternalVariableRepository.detach(
            db=db,
            link=link
        )

    def merge_external_variables(
        self,
        db: Session,
        dataset,
        dataframe: pd.DataFrame,
        date_column: str
    ) -> tuple[
        pd.DataFrame,
        list[dict],
    ]:

        links = (
            DatasetExternalVariableRepository
            .get_links_by_dataset(
                db=db,
                dataset_id=dataset.id
            )
        )

        if not links:

            return (
                dataframe,
                []
            )

        result = dataframe.copy()

        result[
            date_column
        ] = pd.to_datetime(
            result[
                date_column
            ],
            errors="coerce"
        )

        result[
            "__external_merge_date"
        ] = (
            result[
                date_column
            ]
            .dt.normalize()
        )

        business_key = (
            self._resolve_business_key(
                db=db,
                business_series_id=(
                    dataset.business_series_id
                )
            )
        )

        metadata = []

        minimum_date = (
            result[
                "__external_merge_date"
            ]
            .min()
        )

        maximum_date = (
            result[
                "__external_merge_date"
            ]
            .max()
        )

        for link in links:

            variable = (
                ExternalVariableRepository
                .get_by_id(
                    db,
                    link.external_variable_id
                )
            )

            if not variable:
                continue

            if not variable.is_active:
                continue

            variable_type = (
                variable.variable_type
                .strip()
                .lower()
            )

            if (
                variable_type
                not in self.SUPPORTED_ML_TYPES
            ):

                continue

            feature_name = (
                self.build_feature_name(
                    variable.id,
                    variable.name
                )
            )

            values = (
                ExternalVariableValueRepository
                .get_by_variable(
                    db=db,
                    variable_id=(
                        variable.id
                    ),
                    start_date=(
                        minimum_date.to_pydatetime()
                        if pd.notna(
                            minimum_date
                        )
                        else None
                    ),
                    end_date=(
                        maximum_date.to_pydatetime()
                        if pd.notna(
                            maximum_date
                        )
                        else None
                    ),
                    business_key=(
                        business_key
                    ),
                    include_global=True
                )
            )

            value_frame = (
                self._values_to_dataframe(
                    values=values,
                    business_key=(
                        business_key
                    ),
                    feature_name=(
                        feature_name
                    )
                )
            )

            if value_frame.empty:

                result[
                    feature_name
                ] = 0.0

            else:

                result = result.merge(
                    value_frame,
                    how="left",
                    on="__external_merge_date"
                )

                result[
                    feature_name
                ] = pd.to_numeric(
                    result[
                        feature_name
                    ],
                    errors="coerce"
                )

                if (
                    variable_type
                    == "boolean"
                ):

                    result[
                        feature_name
                    ] = (
                        result[
                            feature_name
                        ]
                        .fillna(0.0)
                    )

                else:

                    result[
                        feature_name
                    ] = (
                        result[
                            feature_name
                        ]
                        .interpolate(
                            limit_direction="both"
                        )
                        .ffill()
                        .bfill()
                    )

                    if (
                        result[
                            feature_name
                        ]
                        .isna()
                        .any()
                    ):

                        median = (
                            result[
                                feature_name
                            ]
                            .median()
                        )

                        if pd.isna(
                            median
                        ):
                            median = 0.0

                        result[
                            feature_name
                        ] = (
                            result[
                                feature_name
                            ]
                            .fillna(
                                float(
                                    median
                                )
                            )
                        )

            metadata.append(
                {
                    "variable_id": (
                        variable.id
                    ),
                    "name": (
                        variable.name
                    ),
                    "variable_type": (
                        variable.variable_type
                    ),
                    "source_type": (
                        variable.source_type
                    ),
                    "feature_name": (
                        feature_name
                    ),
                    "business_key": (
                        business_key
                    )
                }
            )

        result = result.drop(
            columns=[
                "__external_merge_date"
            ]
        )

        return (
            result,
            metadata
        )

    @staticmethod
    def inherit_links(
        db: Session,
        source_dataset_id: int,
        target_dataset_id: int
    ) -> None:

        links = (
            DatasetExternalVariableRepository
            .get_links_by_dataset(
                db=db,
                dataset_id=(
                    source_dataset_id
                )
            )
        )

        for link in links:

            DatasetExternalVariableRepository.attach(
                db=db,
                dataset_id=(
                    target_dataset_id
                ),
                external_variable_id=(
                    link.external_variable_id
                )
            )

    @staticmethod
    def _resolve_business_key(
        db: Session,
        business_series_id: int | None
    ) -> str | None:

        if business_series_id is None:
            return None

        series = (
            BusinessSeriesRepository.get_by_id(
                db,
                business_series_id
            )
        )

        if not series:
            return None

        return (
            series.external_entity_id
        )

    @staticmethod
    def _values_to_dataframe(
        values: list,
        business_key: str | None,
        feature_name: str
    ) -> pd.DataFrame:

        if not values:

            return pd.DataFrame(
                columns=[
                    "__external_merge_date",
                    feature_name,
                ]
            )

        records = []

        for value in values:

            records.append(
                {
                    "__external_merge_date": (
                        pd.Timestamp(
                            value.reference_date
                        ).normalize()
                    ),
                    feature_name: (
                        value.numeric_value
                    ),
                    "__specific": int(
                        business_key is not None
                        and value.business_key
                        == business_key
                    ),
                    "__id": value.id
                }
            )

        frame = pd.DataFrame(
            records
        )

        frame = (
            frame
            .sort_values(
                [
                    "__external_merge_date",
                    "__specific",
                    "__id",
                ]
            )
            .drop_duplicates(
                subset=[
                    "__external_merge_date"
                ],
                keep="last"
            )
            .drop(
                columns=[
                    "__specific",
                    "__id",
                ]
            )
        )

        return frame

    @staticmethod
    def build_feature_name(
        variable_id: int,
        variable_name: str
    ) -> str:

        normalized = (
            unicodedata.normalize(
                "NFKD",
                variable_name
            )
            .encode(
                "ascii",
                "ignore"
            )
            .decode(
                "ascii"
            )
            .lower()
        )

        normalized = re.sub(
            r"[^a-z0-9]+",
            "_",
            normalized
        )

        normalized = (
            normalized.strip("_")
            or "variable"
        )

        return (
            f"ext_{variable_id}_"
            f"{normalized}"
        )