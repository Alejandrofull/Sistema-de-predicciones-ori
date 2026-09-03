from fastapi import (
    APIRouter,
    Depends,
)

from sqlalchemy.orm import Session

from app.database.session import (
    get_db,
)

from app.schemas.series_extraction import (
    SeriesExtractionRequest,
    SeriesExtractionResponse,
)

from app.security.permissions import (
    Permissions,
    require_permission,
)

from app.services.audit_service import (
    AuditService,
)

from app.services.series_extraction_service import (
    SeriesExtractionService,
)


router = APIRouter(
    prefix="/datasets",
    tags=["series-extraction"],
)

service = (
    SeriesExtractionService()
)


# ==========================================
# EXTRAER SERIES
# ==========================================

@router.post(
    "/{dataset_id}/extract-series",
    response_model=(
        SeriesExtractionResponse
    ),
)
def extract_series(
    dataset_id: int,
    payload: SeriesExtractionRequest,
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
        service.extract_series(
            db=db,
            dataset_id=dataset_id,
            user_id=current_user.id,
            date_column=(
                payload.date_column
            ),
            entity_column=(
                payload.entity_column
            ),
            target_column=(
                payload.target_column
            ),
            entity_type=(
                payload.entity_type
            ),
            aggregation=(
                payload.aggregation
            ),
            minimum_observations=(
                payload
                .minimum_observations
            ),
        )
    )

    AuditService.log_safe(
        db=db,
        user_id=current_user.id,
        action=(
            "dataset.series.extract"
        ),
        entity="dataset",
        entity_id=dataset_id,
        details={
            "date_column": (
                payload.date_column
            ),
            "entity_column": (
                payload.entity_column
            ),
            "target_column": (
                payload.target_column
            ),
            "entity_type": (
                payload.entity_type
            ),
            "aggregation": (
                payload.aggregation
            ),
            "minimum_observations": (
                payload
                .minimum_observations
            ),
        },
    )

    return result