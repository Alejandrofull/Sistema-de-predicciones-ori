from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from sqlalchemy.orm import Session

from app.database.session import (
    get_db,
)

from app.repositories.prediction_repository import (
    PredictionRepository,
)

from app.repositories.prediction_result_repository import (
    PredictionResultRepository,
)

from app.schemas.prediction import (
    ActualValueUpdate,
    PredictionResponse,
    PredictionResultResponse,
    PredictionRunResponse,
)

from app.security.permissions import (
    Permissions,
    require_permission,
)

from app.services.prediction_service import (
    PredictionService,
)


router = APIRouter(
    prefix="/predictions",
    tags=["predictions"]
)

service = PredictionService()


@router.post(
    "",
    response_model=PredictionRunResponse
)
def run_prediction(
    payload,
    current_user=Depends(
        require_permission(
            Permissions.PREDICTIONS_RUN
        )
    ),
    db: Session = Depends(
        get_db
    )
):
    from app.schemas.prediction import (
        PredictionRequest,
    )

    if not isinstance(
        payload,
        PredictionRequest
    ):
        payload = PredictionRequest(
            **payload
        )

    return service.run_prediction(
        db=db,
        user_id=current_user.id,
        horizon=payload.horizon,
        dataset_id=payload.dataset_id,
        business_series_id=(
            payload.business_series_id
        ),
        clip_negative=(
            payload.clip_negative
        ),
        future_features=(
            payload.future_features
        )
    )


@router.get(
    "",
    response_model=list[
        PredictionResponse
    ]
)
def get_predictions(
    current_user=Depends(
        require_permission(
            Permissions.PREDICTIONS_VIEW
        )
    ),
    db: Session = Depends(
        get_db
    )
):
    return (
        PredictionRepository.get_by_user(
            db=db,
            user_id=current_user.id
        )
    )


@router.get(
    "/{prediction_id}",
    response_model=PredictionResponse
)
def get_prediction(
    prediction_id: int,
    current_user=Depends(
        require_permission(
            Permissions.PREDICTIONS_VIEW
        )
    ),
    db: Session = Depends(
        get_db
    )
):
    prediction = (
        PredictionRepository.get_by_id(
            db,
            prediction_id
        )
    )

    if not prediction:
        raise HTTPException(
            status_code=404,
            detail=(
                "Predicción no encontrada"
            )
        )

    if (
        prediction.user_id
        != current_user.id
    ):
        raise HTTPException(
            status_code=403,
            detail=(
                "No tiene acceso "
                "a esta predicción"
            )
        )

    return prediction


@router.get(
    "/{prediction_id}/results",
    response_model=list[
        PredictionResultResponse
    ]
)
def get_prediction_results(
    prediction_id: int,
    current_user=Depends(
        require_permission(
            Permissions.PREDICTIONS_VIEW
        )
    ),
    db: Session = Depends(
        get_db
    )
):
    prediction = (
        PredictionRepository.get_by_id(
            db,
            prediction_id
        )
    )

    if not prediction:
        raise HTTPException(
            status_code=404,
            detail=(
                "Predicción no encontrada"
            )
        )

    if (
        prediction.user_id
        != current_user.id
    ):
        raise HTTPException(
            status_code=403,
            detail=(
                "No tiene acceso "
                "a esta predicción"
            )
        )

    return (
        PredictionResultRepository
        .get_by_prediction(
            db=db,
            prediction_id=(
                prediction_id
            )
        )
    )


@router.patch(
    "/{prediction_id}/results/"
    "{result_id}/actual",
    response_model=(
        PredictionResultResponse
    )
)
def update_actual_value(
    prediction_id: int,
    result_id: int,
    payload: ActualValueUpdate,
    current_user=Depends(
        require_permission(
            Permissions.PREDICTIONS_RUN
        )
    ),
    db: Session = Depends(
        get_db
    )
):
    prediction = (
        PredictionRepository.get_by_id(
            db,
            prediction_id
        )
    )

    if not prediction:
        raise HTTPException(
            status_code=404,
            detail=(
                "Predicción no encontrada"
            )
        )

    if (
        prediction.user_id
        != current_user.id
    ):
        raise HTTPException(
            status_code=403,
            detail=(
                "No tiene acceso "
                "a esta predicción"
            )
        )

    result = (
        PredictionResultRepository
        .get_by_id(
            db,
            result_id
        )
    )

    if (
        not result
        or result.prediction_id
        != prediction_id
    ):
        raise HTTPException(
            status_code=404,
            detail=(
                "Resultado de predicción "
                "no encontrado"
            )
        )

    return (
        PredictionResultRepository
        .update_actual_value(
            db=db,
            result=result,
            actual_value=(
                payload.actual_value
            )
        )
    )


from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from sqlalchemy.orm import Session

from app.database.session import (
    get_db,
)

from app.repositories.prediction_repository import (
    PredictionRepository,
)

from app.repositories.prediction_result_repository import (
    PredictionResultRepository,
)

from app.schemas.prediction import (
    ActualValueUpdate,
    PredictionRequest,
    PredictionResponse,
    PredictionResultResponse,
    PredictionRunResponse,
)

from app.security.permissions import (
    Permissions,
    require_permission,
)

from app.services.prediction_service import (
    PredictionService,
)


router = APIRouter(
    prefix="/predictions",
    tags=["predictions"]
)

service = PredictionService()


@router.post(
    "",
    response_model=PredictionRunResponse
)
def run_prediction(
    payload: PredictionRequest,

    current_user=Depends(
        require_permission(
            Permissions.PREDICTIONS_RUN
        )
    ),

    db: Session = Depends(
        get_db
    )
):
    return service.run_prediction(
        db=db,
        user_id=current_user.id,
        horizon=payload.horizon,
        dataset_id=payload.dataset_id,
        business_series_id=(
            payload.business_series_id
        ),
        clip_negative=(
            payload.clip_negative
        ),
        future_features=(
            payload.future_features
        )
    )


@router.get(
    "",
    response_model=list[
        PredictionResponse
    ]
)
def get_predictions(
    current_user=Depends(
        require_permission(
            Permissions.PREDICTIONS_VIEW
        )
    ),

    db: Session = Depends(
        get_db
    )
):
    return (
        PredictionRepository.get_by_user(
            db=db,
            user_id=current_user.id
        )
    )


@router.get(
    "/{prediction_id}",
    response_model=PredictionResponse
)
def get_prediction(
    prediction_id: int,

    current_user=Depends(
        require_permission(
            Permissions.PREDICTIONS_VIEW
        )
    ),

    db: Session = Depends(
        get_db
    )
):
    prediction = (
        PredictionRepository.get_by_id(
            db,
            prediction_id
        )
    )

    if not prediction:
        raise HTTPException(
            status_code=404,
            detail=(
                "Predicción no encontrada"
            )
        )

    if (
        prediction.user_id
        != current_user.id
    ):
        raise HTTPException(
            status_code=403,
            detail=(
                "No tiene acceso "
                "a esta predicción"
            )
        )

    return prediction


@router.get(
    "/{prediction_id}/results",
    response_model=list[
        PredictionResultResponse
    ]
)
def get_prediction_results(
    prediction_id: int,

    current_user=Depends(
        require_permission(
            Permissions.PREDICTIONS_VIEW
        )
    ),

    db: Session = Depends(
        get_db
    )
):
    prediction = (
        PredictionRepository.get_by_id(
            db,
            prediction_id
        )
    )

    if not prediction:
        raise HTTPException(
            status_code=404,
            detail=(
                "Predicción no encontrada"
            )
        )

    if (
        prediction.user_id
        != current_user.id
    ):
        raise HTTPException(
            status_code=403,
            detail=(
                "No tiene acceso "
                "a esta predicción"
            )
        )

    return (
        PredictionResultRepository
        .get_by_prediction(
            db=db,
            prediction_id=(
                prediction_id
            )
        )
    )


@router.patch(
    "/{prediction_id}/results/"
    "{result_id}/actual",
    response_model=(
        PredictionResultResponse
    )
)
def update_actual_value(
    prediction_id: int,
    result_id: int,
    payload: ActualValueUpdate,

    current_user=Depends(
        require_permission(
            Permissions.PREDICTIONS_RUN
        )
    ),

    db: Session = Depends(
        get_db
    )
):
    prediction = (
        PredictionRepository.get_by_id(
            db,
            prediction_id
        )
    )

    if not prediction:
        raise HTTPException(
            status_code=404,
            detail=(
                "Predicción no encontrada"
            )
        )

    if (
        prediction.user_id
        != current_user.id
    ):
        raise HTTPException(
            status_code=403,
            detail=(
                "No tiene acceso "
                "a esta predicción"
            )
        )

    result = (
        PredictionResultRepository
        .get_by_id(
            db,
            result_id
        )
    )

    if (
        not result
        or result.prediction_id
        != prediction_id
    ):
        raise HTTPException(
            status_code=404,
            detail=(
                "Resultado de predicción "
                "no encontrado"
            )
        )

    return (
        PredictionResultRepository
        .update_actual_value(
            db=db,
            result=result,
            actual_value=(
                payload.actual_value
            )
        )
    )