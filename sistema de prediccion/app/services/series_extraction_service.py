from pathlib import Path
from tempfile import (
    NamedTemporaryFile,
    TemporaryDirectory,
)

from uuid import uuid4

import pandas as pd

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.data.validation.dataset_validator import (
    DatasetValidator,
)

from app.integrations.supabase.storage_service import (
    SupabaseStorageService,
)

from app.repositories.business_series_repository import (
    BusinessSeriesRepository,
)

from app.repositories.dataset_repository import (
    DatasetRepository,
)

from app.services.import_service import (
    ImportService,
)


class SeriesExtractionService:

    def __init__(self):

        self.storage = (
            SupabaseStorageService(
                bucket="datasets"
            )
        )

        self.import_service = (
            ImportService()
        )

        self.validator = (
            DatasetValidator()
        )

    def extract_series(
        self,
        db: Session,
        dataset_id: int,
        user_id: int,
        date_column: str,
        entity_column: str,
        target_column: str,
        entity_type: str,
        aggregation: str,
        minimum_observations: int
    ) -> dict:

        source_dataset = (
            DatasetRepository.get_by_id(
                db,
                dataset_id
            )
        )

        if not source_dataset:

            raise HTTPException(
                status_code=404,
                detail=(
                    "Dataset no encontrado"
                )
            )

        if (
            source_dataset.user_id
            != user_id
        ):

            raise HTTPException(
                status_code=403,
                detail=(
                    "No tiene acceso "
                    "a este dataset"
                )
            )

        if not source_dataset.storage_path:

            raise HTTPException(
                status_code=400,
                detail=(
                    "El dataset no tiene "
                    "archivo asociado"
                )
            )

        if not source_dataset.file_format:

            raise HTTPException(
                status_code=400,
                detail=(
                    "El dataset no tiene "
                    "formato registrado"
                )
            )

        dataframe = (
            self._load_dataset(
                storage_path=(
                    source_dataset.storage_path
                ),
                file_format=(
                    source_dataset.file_format
                )
            )
        )

        required_columns = {
            date_column,
            entity_column,
            target_column
        }

        missing_columns = (
            required_columns
            - set(
                dataframe.columns
            )
        )

        if missing_columns:

            raise HTTPException(
                status_code=400,
                detail={
                    "message": (
                        "Faltan columnas "
                        "requeridas"
                    ),
                    "missing_columns": sorted(
                        missing_columns
                    )
                }
            )

        dataframe = (
            dataframe[
                [
                    date_column,
                    entity_column,
                    target_column
                ]
            ]
            .copy()
        )

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

        dataframe[
            entity_column
        ] = (
            dataframe[
                entity_column
            ]
            .astype(
                "string"
            )
            .str.strip()
        )

        dataframe = (
            dataframe
            .dropna(
                subset=[
                    date_column,
                    entity_column,
                    target_column
                ]
            )
            .copy()
        )

        dataframe = dataframe[
            dataframe[
                entity_column
            ]
            .str.len()
            > 0
        ].copy()

        if dataframe.empty:

            raise HTTPException(
                status_code=400,
                detail=(
                    "No quedaron registros "
                    "válidos para generar series"
                )
            )

        entities = sorted(
            dataframe[
                entity_column
            ]
            .dropna()
            .unique()
            .tolist()
        )

        extracted_series = []

        skipped_series = []

        for entity_value in entities:

            entity_dataframe = (
                dataframe[
                    dataframe[
                        entity_column
                    ]
                    == entity_value
                ]
                .copy()
            )

            series_dataframe = (
                self._aggregate_series(
                    dataframe=(
                        entity_dataframe
                    ),
                    date_column=(
                        date_column
                    ),
                    target_column=(
                        target_column
                    ),
                    aggregation=(
                        aggregation
                    )
                )
            )

            if (
                len(series_dataframe)
                < minimum_observations
            ):

                skipped_series.append(
                    {
                        "entity": str(
                            entity_value
                        ),
                        "reason": (
                            "insufficient_observations"
                        ),
                        "observations": int(
                            len(
                                series_dataframe
                            )
                        ),
                        "minimum_required": (
                            minimum_observations
                        )
                    }
                )

                continue

            business_series = (
                self._get_or_create_business_series(
                    db=db,
                    entity_value=str(
                        entity_value
                    ),
                    entity_type=(
                        entity_type
                    ),
                    entity_column=(
                        entity_column
                    )
                )
            )

            validation = (
                self.validator.analyze(
                    series_dataframe
                )
            )

            remote_path = (
                self._store_series(
                    dataframe=(
                        series_dataframe
                    ),
                    user_id=user_id,
                    source_dataset_id=(
                        source_dataset.id
                    ),
                    business_series_id=(
                        business_series.id
                    ),
                    entity_name=str(
                        entity_value
                    )
                )
            )

            columns_info = (
                self._build_columns_info(
                    series_dataframe
                )
            )

            safe_name = (
                self._safe_name(
                    str(
                        entity_value
                    )
                )
            )

            dataset_name = (
                f"{source_dataset.name}_"
                f"{safe_name}"
            )

            try:

                derived_dataset = (
                    DatasetRepository.create(
                        db=db,
                        user_id=user_id,
                        parent_dataset_id=(
                            source_dataset.id
                        ),
                        business_series_id=(
                            business_series.id
                        ),
                        name=dataset_name,
                        original_filename=(
                            f"{dataset_name}.parquet"
                        ),
                        file_format="parquet",
                        source_type=(
                            "series_extraction"
                        ),
                        processing_stage=(
                            "raw"
                        ),
                        storage_path=(
                            remote_path
                        ),
                        row_count=int(
                            len(
                                series_dataframe
                            )
                        ),
                        column_count=int(
                            len(
                                series_dataframe.columns
                            )
                        ),
                        columns_info=(
                            columns_info
                        ),
                        quality_report=(
                            validation
                        ),
                        dataset_metadata={
                            "source": (
                                "series_extraction"
                            ),
                            "source_dataset_id": (
                                source_dataset.id
                            ),
                            "business_series_id": (
                                business_series.id
                            ),
                            "entity_column": (
                                entity_column
                            ),
                            "entity_value": str(
                                entity_value
                            ),
                            "entity_type": (
                                entity_type
                            ),
                            "date_column": (
                                date_column
                            ),
                            "target_column": (
                                target_column
                            ),
                            "aggregation": (
                                aggregation
                            )
                        },
                        status=(
                            "ready"
                        )
                    )
                )

            except Exception:

                try:

                    self.storage.remove_file(
                        remote_path
                    )

                except Exception:
                    pass

                raise

            extracted_series.append(
                {
                    "business_series_id": (
                        business_series.id
                    ),
                    "dataset_id": (
                        derived_dataset.id
                    ),
                    "external_entity_id": (
                        business_series
                        .external_entity_id
                    ),
                    "name": (
                        business_series.name
                        or str(
                            entity_value
                        )
                    ),
                    "entity_type": (
                        business_series.entity_type
                    ),
                    "rows": int(
                        len(
                            series_dataframe
                        )
                    ),
                    "date_column": (
                        date_column
                    ),
                    "target_column": (
                        target_column
                    ),
                    "storage_path": (
                        remote_path
                    )
                }
            )

        return {
            "source_dataset_id": (
                source_dataset.id
            ),
            "entity_column": (
                entity_column
            ),
            "entities_detected": (
                len(
                    entities
                )
            ),
            "series_created": (
                len(
                    extracted_series
                )
            ),
            "series_skipped": (
                len(
                    skipped_series
                )
            ),
            "extracted_series": (
                extracted_series
            ),
            "skipped_series": (
                skipped_series
            )
        }

    def _load_dataset(
        self,
        storage_path: str,
        file_format: str
    ) -> pd.DataFrame:

        try:

            file_bytes = (
                self.storage.download_bytes(
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

        try:

            with NamedTemporaryFile(
                delete=False,
                suffix=f".{file_format}"
            ) as tmp:

                tmp.write(
                    file_bytes
                )

                temp_path = Path(
                    tmp.name
                )

            return (
                self.import_service.load(
                    file_format,
                    temp_path
                )
            )

        finally:

            if temp_path:

                temp_path.unlink(
                    missing_ok=True
                )

    @staticmethod
    def _aggregate_series(
        dataframe: pd.DataFrame,
        date_column: str,
        target_column: str,
        aggregation: str
    ) -> pd.DataFrame:

        dataframe = (
            dataframe
            .sort_values(
                date_column
            )
            .copy()
        )

        dataframe[
            date_column
        ] = (
            dataframe[
                date_column
            ]
            .dt.normalize()
        )

        if aggregation == "sum":

            grouped = (
                dataframe
                .groupby(
                    date_column,
                    as_index=False
                )[
                    target_column
                ]
                .sum()
            )

        elif aggregation == "mean":

            grouped = (
                dataframe
                .groupby(
                    date_column,
                    as_index=False
                )[
                    target_column
                ]
                .mean()
            )

        elif aggregation == "max":

            grouped = (
                dataframe
                .groupby(
                    date_column,
                    as_index=False
                )[
                    target_column
                ]
                .max()
            )

        elif aggregation == "min":

            grouped = (
                dataframe
                .groupby(
                    date_column,
                    as_index=False
                )[
                    target_column
                ]
                .min()
            )

        else:

            raise ValueError(
                "Agregación no soportada"
            )

        grouped = (
            grouped
            .sort_values(
                date_column
            )
            .reset_index(
                drop=True
            )
        )

        return grouped

    @staticmethod
    def _get_or_create_business_series(
        db: Session,
        entity_value: str,
        entity_type: str,
        entity_column: str
    ):

        external_entity_id = (
            f"{entity_type}:"
            f"{entity_value}"
        )

        existing = (
            BusinessSeriesRepository
            .get_by_external_entity_id(
                db=db,
                external_entity_id=(
                    external_entity_id
                ),
                entity_type=(
                    entity_type
                )
            )
        )

        if existing:
            return existing

        return (
            BusinessSeriesRepository.create(
                db=db,
                external_entity_id=(
                    external_entity_id
                ),
                entity_type=(
                    entity_type
                ),
                name=entity_value,
                dimensions={
                    "source_column": (
                        entity_column
                    ),
                    "source_value": (
                        entity_value
                    )
                },
                is_active=True
            )
        )

    def _store_series(
        self,
        dataframe: pd.DataFrame,
        user_id: int,
        source_dataset_id: int,
        business_series_id: int,
        entity_name: str
    ) -> str:

        safe_name = (
            self._safe_name(
                entity_name
            )
        )

        filename = (
            f"{safe_name}.parquet"
        )

        remote_path = (
            f"user_{user_id}/"
            f"series/"
            f"source_{source_dataset_id}/"
            f"business_series_"
            f"{business_series_id}/"
            f"{uuid4()}_"
            f"{filename}"
        )

        with TemporaryDirectory() as tmp_dir:

            local_path = (
                Path(
                    tmp_dir
                )
                /
                filename
            )

            dataframe.to_parquet(
                local_path,
                index=False
            )

            self.storage.upload_file(
                local_path=local_path,
                remote_path=remote_path,
                content_type=(
                    "application/octet-stream"
                )
            )

        return remote_path

    @staticmethod
    def _build_columns_info(
        dataframe: pd.DataFrame
    ) -> list[dict]:

        result = []

        for column in dataframe.columns:

            result.append(
                {
                    "name": str(
                        column
                    ),
                    "dtype": str(
                        dataframe[
                            column
                        ].dtype
                    ),
                    "null_count": int(
                        dataframe[
                            column
                        ]
                        .isna()
                        .sum()
                    ),
                    "unique_count": int(
                        dataframe[
                            column
                        ]
                        .nunique(
                            dropna=True
                        )
                    )
                }
            )

        return result

    @staticmethod
    def _safe_name(
        value: str
    ) -> str:

        safe = "".join(
            character
            if (
                character.isalnum()
                or character
                in {
                    "-",
                    "_"
                }
            )
            else "_"
            for character
            in value.strip()
        )

        safe = (
            safe
            .strip(
                "_"
            )
        )

        if not safe:
            return "series"

        return safe[:100]