from fastapi import (
    APIRouter,
    Depends,
)

from sqlalchemy.orm import Session

from app.database.session import (
    get_db
)

from app.schemas.dataset_validation import (
    DatasetValidationResponse
)

from app.security.permissions import (
    Permissions,
    require_permission
)

from app.services.dataset_validation_service import (
    DatasetValidationService
)


router = APIRouter(
    prefix="/datasets",
    tags=["dataset-validation"]
)

service = (
    DatasetValidationService()
)


@router.post(
    "/{dataset_id}/validate",
    response_model=(
        DatasetValidationResponse
    )
)
def validate_dataset(
    dataset_id: int,

    current_user=Depends(
        require_permission(
            Permissions.DATASETS_VIEW
        )
    ),

    db: Session = Depends(
        get_db
    )
):
    return (
        service.validate_dataset(
            db=db,
            dataset_id=dataset_id,
            user_id=current_user.id
        )
    )