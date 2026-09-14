import json

from pathlib import Path
from tempfile import NamedTemporaryFile
from uuid import uuid4

import pandas as pd

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.data.preprocessing.dataset_preprocessor import (
    DatasetPreprocessor,
)

from app.data.validation.dataset_validator import (
    DatasetValidator,
)

from app.integrations.supabase.storage_service import (
    SupabaseStorageService,
)

from app.ml.features.time_series_features import (
    TimeSeriesFeatureEngineer,
)

from app.repositories.dataset_repository import (
    DatasetRepository,
)

from app.services.dataset_external_variable_service import (
    DatasetExternalVariableService,
)

from app.services.import_service import (
    ImportService,
)


class DatasetProcessingService:

    def __init__(self):

        self.import_service = (
            ImportService()
        )

        self.validator = (
            DatasetValidator()
        )

        self.preprocessor = (
            DatasetPreprocessor()
        )

        self.feature_engineer = (
            TimeSeriesFeatureEngineer()
        )

        self.external_variables = (
            DatasetExternalVariableService()
        )

        self.storage = (
            SupabaseStorageService(
                bucket="datasets"
            )
        )

    def process_dataset(
        self,
        db: Session,
        dataset_id: int,
        user_id: int,
        date_column: str | None,
        target_column: str | None,
        remove_duplicates: bool,
        fill_missing_target: bool,
        generate_features: bool,
        lags: list[int],
        rolling_windows: list[int],
        allow_all_users: bool = False
    ) -> dict:

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

        if (
            not allow_all_users
            and dataset.user_id != user_id
        ):

            raise HTTPException(
                status_code=403,
                detail=(
                    "No tiene acceso "
                    "a este dataset"
                )
            )

        if not dataset.storage_path:

            raise HTTPException(
                status_code=400,
                detail=(
                    "El dataset no tiene "
                    "archivo asociado"
                )
            )

        if not dataset.file_format:

            raise HTTPException(
                status_code=400,
                detail=(
                    "El dataset no tiene "
                    "formato registrado"
                )
            )

        try:

            file_bytes = (
                self.storage.download_bytes(
                    dataset.storage_path
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

        source_temp_path = None
        processed_temp_path = None
        remote_path = None

        try:

            with NamedTemporaryFile(
                delete=False,
                suffix=(
                    f".{dataset.file_format}"
                )
            ) as source_tmp:

                source_tmp.write(
                    file_bytes
                )

                source_temp_path = Path(
                    source_tmp.name
                )

            dataframe = (
                self.import_service.load(
                    dataset.file_format,
                    source_temp_path
                )
            )

            validation = (
                self.validator.analyze(
                    dataframe
                )
            )

            metadata = (
                dataset.dataset_metadata
                or {}
            )

            resolved_date_column = (
                date_column
                or metadata.get(
                    "date_column"
                )
                or validation.get(
                    "date_column"
                )
            )

            resolved_target_column = (
                target_column
                or metadata.get(
                    "target_column"
                )
                or validation.get(
                    "target_column"
                )
            )

            if not resolved_date_column:

                raise HTTPException(
                    status_code=400,
                    detail=(
                        "No se pudo determinar "
                        "la columna de fecha"
                    )
                )

            if not resolved_target_column:

                raise HTTPException(
                    status_code=400,
                    detail=(
                        "No se pudo determinar "
                        "la variable objetivo"
                    )
                )

            if (
                resolved_date_column
                not in dataframe.columns
            ):

                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"La columna "
                        f"'{resolved_date_column}' "
                        "no existe"
                    )
                )

            if (
                resolved_target_column
                not in dataframe.columns
            ):

                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"La columna "
                        f"'{resolved_target_column}' "
                        "no existe"
                    )
                )

            (
                dataframe,
                external_variable_metadata
            ) = (
                self.external_variables
                .merge_external_variables(
                    db=db,
                    dataset=dataset,
                    dataframe=dataframe,
                    date_column=(
                        resolved_date_column
                    )
                )
            )

            (
                processed_dataframe,
                preprocessing_report
            ) = (
                self.preprocessor.preprocess(
                    dataframe=dataframe,
                    date_column=(
                        resolved_date_column
                    ),
                    target_column=(
                        resolved_target_column
                    ),
                    remove_duplicates=(
                        remove_duplicates
                    ),
                    fill_missing_target=(
                        fill_missing_target
                    ),
                    sort_by_date=True
                )
            )

            feature_report = None

            if generate_features:

                (
                    processed_dataframe,
                    feature_report
                ) = (
                    self.feature_engineer
                    .create_features(
                        dataframe=(
                            processed_dataframe
                        ),
                        date_column=(
                            resolved_date_column
                        ),
                        target_column=(
                            resolved_target_column
                        ),
                        lags=lags,
                        rolling_windows=(
                            rolling_windows
                        ),
                        drop_generated_na=True
                    )
                )

            processing_stage = (
                "features"
                if generate_features
                else "cleaned"
            )

            suffix_name = (
                "features"
                if generate_features
                else "cleaned"
            )

            processed_name = (
                f"{dataset.name}_"
                f"{suffix_name}"
            )

            filename = (
                f"{processed_name}.parquet"
            )

            with NamedTemporaryFile(
                delete=False,
                suffix=".parquet"
            ) as processed_tmp:

                processed_temp_path = Path(
                    processed_tmp.name
                )

            processed_dataframe.to_parquet(
                processed_temp_path,
                index=False
            )

            remote_path = (
                f"user_{user_id}/"
                f"processed/"
                f"{uuid4()}_"
                f"{filename}"
            )

            self.storage.upload_file(
                local_path=(
                    processed_temp_path
                ),
                remote_path=remote_path,
                content_type=(
                    "application/octet-stream"
                )
            )

            columns_info = (
                self._build_columns_info(
                    processed_dataframe
                )
            )

            quality_report = (
                self.validator.analyze(
                    processed_dataframe
                )
            )

            new_metadata = {
                "source": (
                    "dataset_processing"
                ),
                "parent_dataset_id": (
                    dataset.id
                ),
                "business_series_id": (
                    dataset.business_series_id
                ),
                "date_column": (
                    resolved_date_column
                ),
                "target_column": (
                    resolved_target_column
                ),
                "external_variables": (
                    external_variable_metadata
                ),
                "preprocessing": (
                    preprocessing_report
                ),
                "feature_engineering": (
                    feature_report
                )
            }

            processed_dataset = (
                DatasetRepository.create(
                    db=db,
                    user_id=user_id,
                    parent_dataset_id=(
                        dataset.id
                    ),
                    business_series_id=(
                        dataset.business_series_id
                    ),
                    name=processed_name,
                    original_filename=(
                        filename
                    ),
                    file_format="parquet",
                    source_type="derived",
                    processing_stage=(
                        processing_stage
                    ),
                    storage_path=remote_path,
                    row_count=int(
                        len(
                            processed_dataframe
                        )
                    ),
                    column_count=int(
                        len(
                            processed_dataframe.columns
                        )
                    ),
                    columns_info=(
                        columns_info
                    ),
                    quality_report=(
                        quality_report
                    ),
                    dataset_metadata=(
                        new_metadata
                    ),
                    status="ready"
                )
            )

            (
                DatasetExternalVariableService
                .inherit_links(
                    db=db,
                    source_dataset_id=(
                        dataset.id
                    ),
                    target_dataset_id=(
                        processed_dataset.id
                    )
                )
            )

            preview = (
                self._create_preview(
                    processed_dataframe
                )
            )

            return {
                "source_dataset_id": (
                    dataset.id
                ),
                "processed_dataset_id": (
                    processed_dataset.id
                ),
                "name": (
                    processed_dataset.name
                ),
                "processing_stage": (
                    processing_stage
                ),
                "file_format": "parquet",
                "storage_path": (
                    remote_path
                ),
                "rows": (
                    processed_dataset.row_count
                ),
                "columns": (
                    processed_dataset.column_count
                ),
                "date_column": (
                    resolved_date_column
                ),
                "target_column": (
                    resolved_target_column
                ),
                "preprocessing_report": (
                    preprocessing_report
                ),
                "feature_report": (
                    feature_report
                ),
                "preview": preview
            }

        except Exception:

            if remote_path:

                try:

                    self.storage.remove_file(
                        remote_path
                    )

                except Exception:
                    pass

            raise

        finally:

            if source_temp_path:

                source_temp_path.unlink(
                    missing_ok=True
                )

            if processed_temp_path:

                processed_temp_path.unlink(
                    missing_ok=True
                )

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
    def _create_preview(
        dataframe: pd.DataFrame,
        rows: int = 10
    ) -> list[dict]:

        return json.loads(
            dataframe
            .head(rows)
            .to_json(
                orient="records",
                date_format="iso"
            )
        )