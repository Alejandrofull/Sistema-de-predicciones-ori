from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)

from sqlalchemy.orm import Session

from app.database.session import (
    get_db,
)

from app.repositories.business_series_repository import (
    BusinessSeriesRepository,
)

from app.repositories.dataset_repository import (
    DatasetRepository,
)

from app.schemas.business_series import (
    BusinessSeriesCreateRequest,
    BusinessSeriesDeleteResponse,
    BusinessSeriesResponse,
    BusinessSeriesStatusRequest,
    BusinessSeriesUpdateRequest,
)

from app.schemas.dataset import (
    DatasetResponse,
)

from app.security.permissions import (
    Permissions,
    require_permission,
)

from app.services.audit_service import (
    AuditService,
)

from app.services.business_series_service import (
    BusinessSeriesService,
)


router = APIRouter(
    prefix="/business-series",
    tags=["business-series"]
)


@router.post(
    "",
    response_model=(
        BusinessSeriesResponse
    ),
    status_code=201
)
def create_business_series(
    payload: BusinessSeriesCreateRequest,

    current_user=Depends(
        require_permission(
            Permissions.BUSINESS_SERIES_MANAGE
        )
    ),

    db: Session = Depends(
        get_db
    )
):
    business_series = (
        BusinessSeriesService.create(
            db=db,
            external_entity_id=(
                payload.external_entity_id
            ),
            entity_type=(
                payload.entity_type
            ),
            name=payload.name,
            dimensions=(
                payload.dimensions
            ),
            is_active=(
                payload.is_active
            )
        )
    )

    AuditService.log_safe(
        db=db,
        user_id=current_user.id,
        action="business_series.create",
        entity="business_series",
        entity_id=business_series.id,
        details={
            "external_entity_id": (
                business_series
                .external_entity_id
            ),
            "entity_type": (
                business_series.entity_type
            ),
            "name": (
                business_series.name
            ),
            "is_active": (
                business_series.is_active
            ),
            "dimensions": (
                business_series.dimensions
            ),
        }
    )

    return business_series


@router.get(
    "",
    response_model=list[
        BusinessSeriesResponse
    ]
)
def get_business_series(
    entity_type: str | None = Query(
        default=None
    ),

    include_inactive: bool = Query(
        default=False
    ),

    current_user=Depends(
        require_permission(
            Permissions.BUSINESS_SERIES_VIEW
        )
    ),

    db: Session = Depends(
        get_db
    )
):
    if entity_type:

        return (
            BusinessSeriesRepository
            .get_by_entity_type(
                db=db,
                entity_type=(
                    entity_type
                    .strip()
                    .lower()
                ),
                include_inactive=(
                    include_inactive
                )
            )
        )

    return (
        BusinessSeriesRepository
        .get_all(
            db=db,
            include_inactive=(
                include_inactive
            )
        )
    )


@router.get(
    "/{business_series_id}",
    response_model=(
        BusinessSeriesResponse
    )
)
def get_business_series_by_id(
    business_series_id: int,

    current_user=Depends(
        require_permission(
            Permissions.BUSINESS_SERIES_VIEW
        )
    ),

    db: Session = Depends(
        get_db
    )
):
    business_series = (
        BusinessSeriesRepository
        .get_by_id(
            db,
            business_series_id
        )
    )

    if not business_series:

        raise HTTPException(
            status_code=404,
            detail=(
                "Serie de negocio "
                "no encontrada"
            )
        )

    return business_series


@router.get(
    "/{business_series_id}/datasets",
    response_model=list[
        DatasetResponse
    ]
)
def get_business_series_datasets(
    business_series_id: int,

    current_user=Depends(
        require_permission(
            Permissions.DATASETS_VIEW
        )
    ),

    db: Session = Depends(
        get_db
    )
):
    business_series = (
        BusinessSeriesRepository
        .get_by_id(
            db,
            business_series_id
        )
    )

    if not business_series:

        raise HTTPException(
            status_code=404,
            detail=(
                "Serie de negocio "
                "no encontrada"
            )
        )

    datasets = (
        DatasetRepository
        .get_by_business_series(
            db=db,
            business_series_id=(
                business_series_id
            )
        )
    )

    return [
        dataset
        for dataset in datasets
        if (
            dataset.user_id
            == current_user.id
        )
    ]


@router.put(
    "/{business_series_id}",
    response_model=(
        BusinessSeriesResponse
    )
)
def update_business_series(
    business_series_id: int,
    payload: BusinessSeriesUpdateRequest,

    current_user=Depends(
        require_permission(
            Permissions.BUSINESS_SERIES_MANAGE
        )
    ),

    db: Session = Depends(
        get_db
    )
):
    result = (
        BusinessSeriesService.update(
            db=db,
            business_series_id=(
                business_series_id
            ),
            external_entity_id=(
                payload.external_entity_id
            ),
            entity_type=(
                payload.entity_type
            ),
            name=payload.name,
            dimensions=(
                payload.dimensions
            ),
            is_active=(
                payload.is_active
            )
        )
    )

    AuditService.log_safe(
        db=db,
        user_id=current_user.id,
        action="business_series.update",
        entity="business_series",
        entity_id=business_series_id,
        details={
            "external_entity_id": (
                payload.external_entity_id
            ),
            "entity_type": (
                payload.entity_type
            ),
            "name": (
                payload.name
            ),
            "dimensions": (
                payload.dimensions
            ),
            "is_active": (
                payload.is_active
            ),
        }
    )

    return result


@router.patch(
    "/{business_series_id}/status",
    response_model=(
        BusinessSeriesResponse
    )
)
def update_business_series_status(
    business_series_id: int,
    payload: BusinessSeriesStatusRequest,

    current_user=Depends(
        require_permission(
            Permissions.BUSINESS_SERIES_MANAGE
        )
    ),

    db: Session = Depends(
        get_db
    )
):
    result = (
        BusinessSeriesService.set_status(
            db=db,
            business_series_id=(
                business_series_id
            ),
            is_active=(
                payload.is_active
            )
        )
    )

    AuditService.log_safe(
        db=db,
        user_id=current_user.id,
        action=(
            "business_series.status.update"
        ),
        entity="business_series",
        entity_id=business_series_id,
        details={
            "is_active": (
                payload.is_active
            )
        }
    )

    return result


@router.delete(
    "/{business_series_id}",
    response_model=(
        BusinessSeriesDeleteResponse
    )
)
def delete_business_series(
    business_series_id: int,

    current_user=Depends(
        require_permission(
            Permissions.BUSINESS_SERIES_MANAGE
        )
    ),

    db: Session = Depends(
        get_db
    )
):
    business_series = (
        BusinessSeriesRepository.get_by_id(
            db,
            business_series_id
        )
    )

    details = None

    if business_series:

        details = {
            "external_entity_id": (
                business_series
                .external_entity_id
            ),
            "entity_type": (
                business_series.entity_type
            ),
            "name": (
                business_series.name
            ),
        }

    BusinessSeriesService.delete(
        db=db,
        business_series_id=(
            business_series_id
        )
    )

    AuditService.log_safe(
        db=db,
        user_id=current_user.id,
        action="business_series.delete",
        entity="business_series",
        entity_id=business_series_id,
        details=details
    )

    return {
        "message": (
            "Serie de negocio "
            "eliminada correctamente"
        )
    }