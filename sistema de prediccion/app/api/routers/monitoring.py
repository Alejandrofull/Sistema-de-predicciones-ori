from fastapi import (
    APIRouter,
    Depends,
    Query,
)

from sqlalchemy.orm import Session

from app.database.session import (
    get_db,
)

from app.schemas.monitoring import (
    ProductionPerformanceResponse,
)

from app.security.permissions import (
    Permissions,
    require_permission,
)

from app.services.performance_monitoring_service import (
    PerformanceMonitoringService,
)


router = APIRouter(
    prefix="/monitoring",
    tags=["monitoring"]
)

service = (
    PerformanceMonitoringService()
)


@router.get(
    "/models/{model_id}/performance",
    response_model=(
        ProductionPerformanceResponse
    )
)
def get_model_performance(
    model_id: int,

    limit: int = Query(
        default=100,
        ge=1,
        le=5000
    ),

    minimum_observations: int = Query(
        default=5,
        ge=2,
        le=1000
    ),

    rmse_degradation_threshold: float = Query(
        default=0.20,
        ge=0.0,
        le=10.0
    ),

    mape_threshold: float = Query(
        default=20.0,
        ge=0.0,
        le=1000.0
    ),

    current_user=Depends(
        require_permission(
            Permissions.DRIFT_VIEW
        )
    ),

    db: Session = Depends(
        get_db
    )
):
    return (
        service.get_model_performance(
            db=db,
            model_id=(
                model_id
            ),
            limit=(
                limit
            ),
            minimum_observations=(
                minimum_observations
            ),
            rmse_degradation_threshold=(
                rmse_degradation_threshold
            ),
            mape_threshold=(
                mape_threshold
            )
        )
    )


@router.get(
    "/business-series/"
    "{business_series_id}/performance",
    response_model=(
        ProductionPerformanceResponse
    )
)
def get_business_series_performance(
    business_series_id: int,

    limit: int = Query(
        default=100,
        ge=1,
        le=5000
    ),

    minimum_observations: int = Query(
        default=5,
        ge=2,
        le=1000
    ),

    rmse_degradation_threshold: float = Query(
        default=0.20,
        ge=0.0,
        le=10.0
    ),

    mape_threshold: float = Query(
        default=20.0,
        ge=0.0,
        le=1000.0
    ),

    current_user=Depends(
        require_permission(
            Permissions.DRIFT_VIEW
        )
    ),

    db: Session = Depends(
        get_db
    )
):
    return (
        service
        .get_business_series_performance(
            db=db,
            business_series_id=(
                business_series_id
            ),
            limit=(
                limit
            ),
            minimum_observations=(
                minimum_observations
            ),
            rmse_degradation_threshold=(
                rmse_degradation_threshold
            ),
            mape_threshold=(
                mape_threshold
            )
        )
    )


@router.get(
    "/predictions/"
    "{prediction_id}/performance",
    response_model=(
        ProductionPerformanceResponse
    )
)
def get_prediction_performance(
    prediction_id: int,

    minimum_observations: int = Query(
        default=2,
        ge=2,
        le=1000
    ),

    rmse_degradation_threshold: float = Query(
        default=0.20,
        ge=0.0,
        le=10.0
    ),

    mape_threshold: float = Query(
        default=20.0,
        ge=0.0,
        le=1000.0
    ),

    current_user=Depends(
        require_permission(
            Permissions.DRIFT_VIEW
        )
    ),

    db: Session = Depends(
        get_db
    )
):
    return (
        service.get_prediction_performance(
            db=db,
            prediction_id=(
                prediction_id
            ),
            minimum_observations=(
                minimum_observations
            ),
            rmse_degradation_threshold=(
                rmse_degradation_threshold
            ),
            mape_threshold=(
                mape_threshold
            )
        )
    )