from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from sqlalchemy.orm import Session

from app.database.session import (
    get_db,
)

from app.repositories.dataset_repository import (
    DatasetRepository,
)

from app.schemas.dataset import (
    DatasetDeleteResponse,
    DatasetDownloadResponse,
    DatasetResponse,
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
    prefix="/datasets",
    tags=["datasets"],
)

service = DatasetService()


# ==========================================
# LISTAR DATASETS
# ==========================================

@router.get(
    "",
    response_model=list[
        DatasetResponse
    ],
)
def get_datasets(
    current_user=Depends(
        require_permission(
            Permissions.DATASETS_VIEW
        )
    ),
    db: Session = Depends(
        get_db
    ),
):

    return (
        DatasetRepository
        .get_by_user(
            db=db,
            user_id=current_user.id,
        )
    )


# ==========================================
# OBTENER DATASET
# ==========================================

@router.get(
    "/{dataset_id}",
    response_model=DatasetResponse,
)
def get_dataset(
    dataset_id: int,
    current_user=Depends(
        require_permission(
            Permissions.DATASETS_VIEW
        )
    ),
    db: Session = Depends(
        get_db
    ),
):

    dataset = (
        DatasetRepository
        .get_by_id(
            db,
            dataset_id,
        )
    )

    if not dataset:

        raise HTTPException(
            status_code=404,
            detail="Dataset no encontrado",
        )

    if (
        dataset.user_id
        != current_user.id
    ):

        raise HTTPException(
            status_code=403,
            detail=(
                "No tiene acceso "
                "a este dataset"
            ),
        )

    return dataset


# ==========================================
# DESCARGAR DATASET
# ==========================================

@router.get(
    "/{dataset_id}/download",
    response_model=(
        DatasetDownloadResponse
    ),
)
def download_dataset(
    dataset_id: int,
    current_user=Depends(
        require_permission(
            Permissions.DATASETS_VIEW
        )
    ),
    db: Session = Depends(
        get_db
    ),
):

    return (
        service.get_download_url(
            db=db,
            dataset_id=dataset_id,
            user_id=current_user.id,
        )
    )


# ==========================================
# ELIMINAR DATASET
# ==========================================

@router.delete(
    "/{dataset_id}",
    response_model=(
        DatasetDeleteResponse
    ),
)
def delete_dataset(
    dataset_id: int,
    current_user=Depends(
        require_permission(
            Permissions.DATASETS_DELETE
        )
    ),
    db: Session = Depends(
        get_db
    ),
):

    # Guardamos metadata mínima antes
    # de eliminar el registro.

    dataset = (
        DatasetRepository
        .get_by_id(
            db,
            dataset_id,
        )
    )

    dataset_name = (
        dataset.name
        if dataset
        else None
    )

    business_series_id = (
        dataset.business_series_id
        if dataset
        else None
    )

    processing_stage = (
        dataset.processing_stage
        if dataset
        else None
    )

    service.delete_dataset(
        db=db,
        dataset_id=dataset_id,
        user_id=current_user.id,
    )

    AuditService.log_safe(
        db=db,
        user_id=current_user.id,
        action="dataset.delete",
        entity="dataset",
        entity_id=dataset_id,
        details={
            "name": (
                dataset_name
            ),
            "business_series_id": (
                business_series_id
            ),
            "processing_stage": (
                processing_stage
            ),
        },
    )

    return {
        "message": (
            "Dataset eliminado correctamente"
        )
    }