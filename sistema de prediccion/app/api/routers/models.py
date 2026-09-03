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

from app.repositories.model_evaluation_repository import (
    ModelEvaluationRepository,
)

from app.repositories.model_repository import (
    ModelRepository,
)

from app.repositories.model_version_repository import (
    ModelVersionRepository,
)

from app.schemas.model import (
    MLModelResponse,
    ModelActivationResponse,
    ModelEvaluationResponse,
    ModelVersionResponse,
)

from app.security.permissions import (
    Permissions,
    require_permission,
)

from app.services.audit_service import (
    AuditService,
)

from app.services.model_management_service import (
    ModelManagementService,
)


router = APIRouter(
    prefix="/models",
    tags=["models"]
)


@router.get(
    "",
    response_model=list[
        MLModelResponse
    ]
)
def get_models(
    business_series_id: int | None = Query(
        default=None,
        gt=0
    ),

    current_user=Depends(
        require_permission(
            Permissions.MODELS_VIEW
        )
    ),

    db: Session = Depends(
        get_db
    )
):
    if business_series_id is not None:

        return (
            ModelRepository
            .get_by_business_series(
                db=db,
                business_series_id=(
                    business_series_id
                )
            )
        )

    return (
        ModelRepository.get_all(
            db
        )
    )


@router.get(
    "/active",
    response_model=(
        MLModelResponse | None
    )
)
def get_active_model(
    business_series_id: int | None = Query(
        default=None,
        gt=0
    ),

    current_user=Depends(
        require_permission(
            Permissions.MODELS_VIEW
        )
    ),

    db: Session = Depends(
        get_db
    )
):
    if business_series_id is not None:

        return (
            ModelRepository
            .get_active_by_business_series(
                db=db,
                business_series_id=(
                    business_series_id
                )
            )
        )

    return (
        ModelRepository
        .get_active_global(
            db
        )
    )


@router.get(
    "/{model_id}",
    response_model=MLModelResponse
)
def get_model(
    model_id: int,

    current_user=Depends(
        require_permission(
            Permissions.MODELS_VIEW
        )
    ),

    db: Session = Depends(
        get_db
    )
):
    model = (
        ModelRepository.get_by_id(
            db,
            model_id
        )
    )

    if not model:

        raise HTTPException(
            status_code=404,
            detail="Modelo no encontrado"
        )

    return model


@router.get(
    "/{model_id}/versions",
    response_model=list[
        ModelVersionResponse
    ]
)
def get_model_versions(
    model_id: int,

    current_user=Depends(
        require_permission(
            Permissions.MODELS_VIEW
        )
    ),

    db: Session = Depends(
        get_db
    )
):
    model = (
        ModelRepository.get_by_id(
            db,
            model_id
        )
    )

    if not model:

        raise HTTPException(
            status_code=404,
            detail="Modelo no encontrado"
        )

    return (
        ModelVersionRepository
        .get_by_model(
            db=db,
            model_id=model_id
        )
    )


@router.get(
    "/{model_id}/evaluations",
    response_model=list[
        ModelEvaluationResponse
    ]
)
def get_model_evaluations(
    model_id: int,

    current_user=Depends(
        require_permission(
            Permissions.MODELS_VIEW
        )
    ),

    db: Session = Depends(
        get_db
    )
):
    model = (
        ModelRepository.get_by_id(
            db,
            model_id
        )
    )

    if not model:

        raise HTTPException(
            status_code=404,
            detail="Modelo no encontrado"
        )

    return (
        ModelEvaluationRepository
        .get_by_model(
            db=db,
            model_id=model_id
        )
    )


@router.post(
    "/{model_id}/activate",
    response_model=(
        ModelActivationResponse
    )
)
def activate_model(
    model_id: int,

    current_user=Depends(
        require_permission(
            Permissions.MODELS_ACTIVATE
        )
    ),

    db: Session = Depends(
        get_db
    )
):
    result = (
        ModelManagementService
        .activate_model(
            db=db,
            model_id=model_id,
            user_id=current_user.id
        )
    )

    model = (
        ModelRepository.get_by_id(
            db,
            model_id
        )
    )

    AuditService.log_safe(
        db=db,
        user_id=current_user.id,
        action="model.activate",
        entity="model",
        entity_id=model_id,
        details={
            "model_type": (
                model.model_type
                if model
                else None
            ),
            "business_series_id": (
                model.business_series_id
                if model
                else None
            ),
            "version": (
                model.version
                if model
                else None
            ),
        }
    )

    return result