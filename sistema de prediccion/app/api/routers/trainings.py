from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)

from fastapi.concurrency import run_in_threadpool

from sqlalchemy.orm import Session

from app.database.session import (
    get_db,
)

from app.repositories.training_repository import (
    TrainingRepository,
)

from app.schemas.training import (
    TrainingRequest,
    TrainingResponse,
    TrainingRunResponse,
)

from app.security.dependencies import (
    user_can_manage_all_datasets,
)

from app.security.permissions import (
    Permissions,
    require_permission,
)

from app.services.audit_service import (
    AuditService,
)

from app.services.notification_dispatch_service import (
    NotificationDispatchService,
)

from app.services.training_service import (
    TrainingService,
)


router = APIRouter(
    prefix="/trainings",
    tags=["trainings"]
)

service = TrainingService()


@router.post(
    "",
    response_model=TrainingRunResponse
)
async def create_training(
    payload: TrainingRequest,

    current_user=Depends(
        require_permission(
            Permissions.MODELS_TRAIN
        )
    ),

    db: Session = Depends(
        get_db
    )
):
    # train_models es síncrona (SQLAlchemy sync, I/O de storage,
    # entrenamiento de modelos); se corre en threadpool para no
    # bloquear el event loop. Ya no dispatcha notificaciones por
    # dentro: solo las crea y las devuelve.
    result, notifications_to_dispatch = await run_in_threadpool(
        service.train_models,
        db=db,
        dataset_id=payload.dataset_id,
        user_id=current_user.id,
        date_column=payload.date_column,
        target_column=payload.target_column,
        model_names=payload.model_names,
        test_ratio=payload.test_ratio,
        allow_all_users=user_can_manage_all_datasets(db, current_user.id),
    )

    for notification in notifications_to_dispatch:

        await NotificationDispatchService.dispatch(
            db=db,
            notification=notification
        )

    await run_in_threadpool(
        AuditService.log_safe,
        db=db,
        user_id=current_user.id,
        action="model.train",
        entity="dataset",
        entity_id=payload.dataset_id,
        details={
            "dataset_id": (
                payload.dataset_id
            ),
            "date_column": (
                payload.date_column
            ),
            "target_column": (
                payload.target_column
            ),
            "model_names": (
                payload.model_names
            ),
            "test_ratio": (
                payload.test_ratio
            ),
            "business_series_id": (
                result.get(
                    "business_series_id"
                )
            ),
            "winner": (
                result.get(
                    "winner"
                )
            ),
            "winner_model_id": (
                result.get(
                    "winner_model_id"
                )
            ),
            "ranking": (
                result.get(
                    "ranking"
                )
            ),
            "ranking_metric": (
                result.get(
                    "ranking_metric"
                )
            ),
            "winner_selection_rmse": (
                result.get(
                    "winner_selection_rmse"
                )
            ),
            "errors": (
                result.get(
                    "errors"
                )
            ),
        }
    )

    return result


@router.get(
    "",
    response_model=list[
        TrainingResponse
    ]
)
def get_trainings(
    dataset_id: int | None = Query(
        default=None
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
    if dataset_id is not None:

        return (
            TrainingRepository.get_by_dataset(
                db,
                dataset_id
            )
        )

    return (
        TrainingRepository.get_all(
            db
        )
    )


@router.get(
    "/{training_id}",
    response_model=TrainingResponse
)
def get_training(
    training_id: int,

    current_user=Depends(
        require_permission(
            Permissions.MODELS_VIEW
        )
    ),

    db: Session = Depends(
        get_db
    )
):
    training = (
        TrainingRepository.get_by_id(
            db,
            training_id
        )
    )

    if not training:

        raise HTTPException(
            status_code=404,
            detail=(
                "Entrenamiento no encontrado"
            )
        )

    return training