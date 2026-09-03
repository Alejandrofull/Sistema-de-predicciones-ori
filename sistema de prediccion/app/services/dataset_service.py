from pathlib import Path
from uuid import uuid4

from fastapi import (
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app.integrations.supabase.storage_service import (
    SupabaseStorageService
)
from app.repositories.dataset_repository import (
    DatasetRepository
)
from app.services.import_service import (
    ImportService
)


class DatasetService:

    ALLOWED_EXTENSIONS = {
        "csv",
        "xlsx",
        "xls",
        "json",
        "parquet",
    }

    def __init__(self):
        self.import_service = ImportService()

        self.storage = (
            SupabaseStorageService(
                bucket="datasets"
            )
        )

    def process_file(
        self,
        db: Session,
        user_id: int,
        original_filename: str,
        suffix: str,
        temp_path: Path
    ) -> dict:

        suffix = (
            suffix
            .lower()
            .strip()
            .lstrip(".")
        )

        if suffix not in self.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=(
                    status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
                ),
                detail=(
                    "Formato no soportado: "
                    f"{suffix}"
                )
            )

        try:
            dataframe = (
                self.import_service.load(
                    suffix,
                    temp_path
                )
            )

        except Exception as error:
            raise HTTPException(
                status_code=400,
                detail=(
                    "No se pudo leer el dataset: "
                    f"{error}"
                )
            )

        if dataframe.empty:
            raise HTTPException(
                status_code=400,
                detail=(
                    "El dataset no contiene registros"
                )
            )

        columns = [
            str(column)
            for column in dataframe.columns
        ]

        columns_info = []

        for column in dataframe.columns:

            columns_info.append(
                {
                    "name": str(column),
                    "dtype": str(
                        dataframe[column].dtype
                    ),
                    "null_count": int(
                        dataframe[column]
                        .isna()
                        .sum()
                    ),
                    "unique_count": int(
                        dataframe[column]
                        .nunique(
                            dropna=True
                        )
                    )
                }
            )

        quality_report = (
            self.import_service
            .quality_report(
                dataframe
            )
        )

        remote_path = (
            f"user_{user_id}/"
            f"{uuid4()}_"
            f"{Path(original_filename).name}"
        )

        try:
            self.storage.upload_file(
                local_path=temp_path,
                remote_path=remote_path
            )

        except Exception as error:
            raise HTTPException(
                status_code=500,
                detail=(
                    "No se pudo almacenar "
                    "el dataset en Supabase: "
                    f"{error}"
                )
            )

        try:
            dataset = (
                DatasetRepository.create(
                    db=db,
                    user_id=user_id,
                    name=Path(
                        original_filename
                    ).stem,
                    original_filename=(
                        original_filename
                    ),
                    file_format=suffix,
                    source_type="file",
                    storage_path=remote_path,
                    row_count=len(
                        dataframe
                    ),
                    column_count=len(
                        dataframe.columns
                    ),
                    columns_info=columns_info,
                    quality_report=(
                        quality_report
                    ),
                    dataset_metadata={
                        "source": "upload",
                        "original_filename": (
                            original_filename
                        )
                    },
                    status="ready"
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

        preview_dataframe = (
            dataframe
            .head(10)
            .copy()
        )

        preview_dataframe = (
            preview_dataframe
            .where(
                preview_dataframe.notna(),
                None
            )
        )

        preview = (
            preview_dataframe
            .to_dict(
                orient="records"
            )
        )

        return {
            "id": dataset.id,
            "name": dataset.name,
            "original_filename": (
                dataset.original_filename
            ),
            "file_format": (
                dataset.file_format
            ),
            "row_count": (
                dataset.row_count
            ),
            "column_count": (
                dataset.column_count
            ),
            "columns": columns,
            "quality_report": (
                quality_report
            ),
            "storage_path": (
                remote_path
            ),
            "status": (
                dataset.status
            ),
            "preview": preview
        }

    def get_download_url(
        self,
        db: Session,
        dataset_id: int,
        user_id: int,
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
                status_code=404,
                detail=(
                    "El dataset no tiene "
                    "archivo almacenado"
                )
            )

        try:
            url = (
                self.storage
                .create_signed_url(
                    dataset.storage_path,
                    expires_in=3600
                )
            )

        except Exception as error:
            raise HTTPException(
                status_code=500,
                detail=(
                    "No se pudo generar "
                    "la URL de descarga: "
                    f"{error}"
                )
            )

        return {
            "id": dataset.id,
            "filename": (
                dataset.original_filename
                or dataset.name
            ),
            "download_url": url,
            "expires_in": 3600
        }

    def delete_dataset(
        self,
        db: Session,
        dataset_id: int,
        user_id: int,
        allow_all_users: bool = False
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

        if dataset.storage_path:

            try:
                self.storage.remove_file(
                    dataset.storage_path
                )

            except Exception as error:
                raise HTTPException(
                    status_code=500,
                    detail=(
                        "No se pudo eliminar "
                        "el archivo de Storage: "
                        f"{error}"
                    )
                )

        DatasetRepository.delete(
            db=db,
            dataset=dataset
        )