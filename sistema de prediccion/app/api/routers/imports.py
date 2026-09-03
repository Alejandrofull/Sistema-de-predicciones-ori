from pathlib import Path
from tempfile import (
    NamedTemporaryFile,
)

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
)

from sqlalchemy.orm import Session

from app.database.session import (
    get_db,
)

from app.schemas.dataset import (
    DatasetUploadResponse,
)

from app.security.permissions import (
    Permissions,
    require_permission,
)

from app.services.audit_service import (
    AuditService,
)

from app.services.dataset_service import (
    DatasetService,
)


router = APIRouter(
    prefix="/imports",
    tags=["data-imports"],
)

service = DatasetService()


ALLOWED_EXTENSIONS = {
    "csv",
    "xlsx",
    "xls",
    "json",
    "parquet",
}


# ==========================================
# FORMATOS SOPORTADOS
# ==========================================

@router.get(
    "/formats"
)
def supported_formats(
    current_user=Depends(
        require_permission(
            Permissions.DATASETS_VIEW
        )
    ),
):

    return {
        "files": sorted(
            ALLOWED_EXTENSIONS
        ),
        "sources": [
            "file",
            "database",
            "api",
        ],
        "pipeline": [
            "ingestion",
            "validation",
            "cleaning",
            "transformation",
            "feature_engineering",
            "training",
            "evaluation",
            "prediction",
            "export",
            "reporting",
        ],
    }


# ==========================================
# IMPORTAR ARCHIVO
# ==========================================

@router.post(
    "/file",
    response_model=(
        DatasetUploadResponse
    ),
)
async def import_file(
    file: UploadFile = File(...),
    current_user=Depends(
        require_permission(
            Permissions.DATASETS_IMPORT
        )
    ),
    db: Session = Depends(
        get_db
    ),
):

    original_filename = (
        file.filename
        or "dataset"
    )

    suffix = (
        Path(
            original_filename
        )
        .suffix
        .lower()
        .lstrip(".")
    )

    if (
        suffix
        not in ALLOWED_EXTENSIONS
    ):

        raise HTTPException(
            status_code=415,
            detail=(
                "Formato no soportado: "
                f"{suffix or 'sin extensión'}"
            ),
        )

    temp_path = None

    try:

        with NamedTemporaryFile(
            delete=False,
            suffix=(
                f".{suffix}"
            ),
        ) as tmp:

            while True:

                chunk = (
                    await file.read(
                        1024
                        *
                        1024
                    )
                )

                if not chunk:
                    break

                tmp.write(
                    chunk
                )

            temp_path = Path(
                tmp.name
            )

        result = (
            service.process_file(
                db=db,
                user_id=current_user.id,
                original_filename=(
                    original_filename
                ),
                suffix=suffix,
                temp_path=temp_path,
            )
        )

        dataset_id = (
            _extract_dataset_id(
                result
            )
        )

        AuditService.log_safe(
            db=db,
            user_id=current_user.id,
            action="dataset.import",
            entity="dataset",
            entity_id=dataset_id,
            details={
                "original_filename": (
                    original_filename
                ),
                "file_format": (
                    suffix
                ),
                "source_type": (
                    "file"
                ),
            },
        )

        return result

    finally:

        await file.close()

        if temp_path:

            temp_path.unlink(
                missing_ok=True
            )


# ==========================================
# EXTRAER ID DEL RESULTADO
#
# Compatible con:
# ORM / Pydantic / dict.
# ==========================================

def _extract_dataset_id(
    result
) -> int | None:

    if result is None:
        return None

    for attribute in (
        "dataset_id",
        "id",
    ):

        value = getattr(
            result,
            attribute,
            None,
        )

        if value is not None:

            try:
                return int(
                    value
                )

            except (
                TypeError,
                ValueError,
            ):
                pass

    if isinstance(
        result,
        dict,
    ):

        for key in (
            "dataset_id",
            "id",
        ):

            value = result.get(
                key
            )

            if value is not None:

                try:
                    return int(
                        value
                    )

                except (
                    TypeError,
                    ValueError,
                ):
                    pass

        nested_dataset = (
            result.get(
                "dataset"
            )
        )

        if nested_dataset:

            return (
                _extract_dataset_id(
                    nested_dataset
                )
            )

    return None