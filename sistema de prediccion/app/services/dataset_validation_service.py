from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.data.validation.dataset_validator import (
    DatasetValidator
)
from app.integrations.supabase.client import (
    supabase_admin
)
from app.repositories.dataset_repository import (
    DatasetRepository
)
from app.services.import_service import (
    ImportService
)


class DatasetValidationService:

    def __init__(self):
        self.validator = (
            DatasetValidator()
        )

        self.import_service = (
            ImportService()
        )

    def validate_dataset(
        self,
        db: Session,
        dataset_id: int,
        user_id: int,
        allow_all_users: bool = False
    ) -> dict:

        dataset = (
            DatasetRepository
            .get_by_id(
                db,
                dataset_id
            )
        )

        if not dataset:
            raise HTTPException(
                status_code=404,
                detail=(
                    "Dataset no encontrado"
                )
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
                supabase_admin
                .storage
                .from_(
                    "datasets"
                )
                .download(
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

        temp_path = None

        try:
            with NamedTemporaryFile(
                delete=False,
                suffix=(
                    f".{dataset.file_format}"
                )
            ) as tmp:

                tmp.write(
                    file_bytes
                )

                temp_path = Path(
                    tmp.name
                )

            dataframe = (
                self.import_service
                .load(
                    dataset.file_format,
                    temp_path
                )
            )

            result = (
                self.validator
                .analyze(
                    dataframe
                )
            )

            dataset.quality_report = (
                result
            )

            dataset.status = (
                "ready"
                if result[
                    "is_trainable"
                ]
                else "failed"
            )

            db.commit()
            db.refresh(
                dataset
            )

            return {
                "dataset_id": (
                    dataset.id
                ),
                **result
            }

        finally:

            if temp_path:
                temp_path.unlink(
                    missing_ok=True
                )