from fastapi import (
    APIRouter,
    Depends,
)

from sqlalchemy.orm import Session

from app.database.session import (
    get_db,
)

from app.schemas.dataset_processing import (
    DatasetProcessingRequest,
    DatasetProcessingResponse,
)

from app.security.permissions import (
    Permissions,
    require_permission,
)

from app.services.audit_service import (
    AuditService,
)

from app.services.dataset_processing_service import (
    DatasetProcessingService,
)


router = APIRouter(
    prefix="/datasets",
    tags=["dataset-processing"],
)

service = (
    DatasetProcessingService()
)


# ==========================================
# PROCESAR DATASET
# ==========================================

@router.post(
    "/{dataset_id}/process",
    response_model=(
        DatasetProcessingResponse
    ),
)
def process_dataset(
    dataset_id: int,
    payload: DatasetProcessingRequest,
    current_user=Depends(
        require_permission(
            Permissions.DATASETS_PROCESS
        )
    ),
    db: Session = Depends(
        get_db
    ),
):

    result = (
        service.process_dataset(
            db=db,
            dataset_id=dataset_id,
            user_id=current_user.id,
            date_column=(
                payload.date_column
            ),
            target_column=(
                payload.target_column
            ),
            remove_duplicates=(
                payload.remove_duplicates
            ),
            fill_missing_target=(
                payload.fill_missing_target
            ),
            generate_features=(
                payload.generate_features
            ),
            lags=(
                payload.lags
            ),
            rolling_windows=(
                payload.rolling_windows
            ),
        )
    )

    AuditService.log_safe(
        db=db,
        user_id=current_user.id,
        action="dataset.process",
        entity="dataset",
        entity_id=dataset_id,
        details={
            "date_column": (
                payload.date_column
            ),
            "target_column": (
                payload.target_column
            ),
            "remove_duplicates": (
                payload.remove_duplicates
            ),
            "fill_missing_target": (
                payload.fill_missing_target
            ),
            "generate_features": (
                payload.generate_features
            ),
            "lags": (
                payload.lags
            ),
            "rolling_windows": (
                payload.rolling_windows
            ),
        },
    )

    return result