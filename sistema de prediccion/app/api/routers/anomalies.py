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

from app.repositories.anomaly_repository import (
    AnomalyRepository,
)

from app.schemas.anomaly import (
    AnomalyDetectionResponse,
    AnomalyResponse,
    AnomalyStatusResponse,
)

from app.security.permissions import (
    Permissions,
    require_permission,
)

from app.services.anomaly_service import (
    AnomalyService,
)

from app.services.audit_service import (
    AuditService,
)


router = APIRouter(
    prefix="/anomalies",
    tags=["anomalies"]
)

service = AnomalyService()


@router.post(
    "/scan",
    response_model=(
        AnomalyDetectionResponse
    )
)
def scan_anomalies(
    business_series_id: int | None = Query(
        default=None,
        gt=0
    ),

    model_id: int | None = Query(
        default=None,
        gt=0
    ),

    limit: int = Query(
        default=200,
        ge=10,
        le=5000
    ),

    minimum_observations: int = Query(
        default=10,
        ge=5,
        le=1000
    ),

    z_threshold: float = Query(
        default=3.0,
        ge=1.0,
        le=10.0
    ),

    iqr_multiplier: float = Query(
        default=1.5,
        ge=0.5,
        le=10.0
    ),

    current_user=Depends(
        require_permission(
            Permissions.ANOMALIES_SCAN
        )
    ),

    db: Session = Depends(
        get_db
    )
):
    result = (
        service.scan_prediction_errors(
            db=db,
            business_series_id=(
                business_series_id
            ),
            model_id=model_id,
            limit=limit,
            minimum_observations=(
                minimum_observations
            ),
            z_threshold=(
                z_threshold
            ),
            iqr_multiplier=(
                iqr_multiplier
            )
        )
    )

    AuditService.log_safe(
        db=db,
        user_id=current_user.id,
        action="anomaly.scan",
        entity="business_series",
        entity_id=(
            business_series_id
        ),
        details={
            "business_series_id": (
                business_series_id
            ),
            "model_id": (
                model_id
            ),
            "limit": (
                limit
            ),
            "minimum_observations": (
                minimum_observations
            ),
            "z_threshold": (
                z_threshold
            ),
            "iqr_multiplier": (
                iqr_multiplier
            ),
            "observations_analyzed": (
                result.get(
                    "observations_analyzed"
                )
            ),
            "anomalies_detected": (
                result.get(
                    "anomalies_detected"
                )
            ),
            "anomalies_created": (
                result.get(
                    "anomalies_created"
                )
            ),
            "notifications_created": (
                result.get(
                    "notifications_created"
                )
            ),
        }
    )

    return result


@router.get(
    "",
    response_model=list[
        AnomalyResponse
    ]
)
def get_anomalies(
    business_series_id: int | None = Query(
        default=None,
        gt=0
    ),

    model_id: int | None = Query(
        default=None,
        gt=0
    ),

    status: str | None = Query(
        default=None
    ),

    limit: int = Query(
        default=100,
        ge=1,
        le=5000
    ),

    current_user=Depends(
        require_permission(
            Permissions.ANOMALIES_VIEW
        )
    ),

    db: Session = Depends(
        get_db
    )
):
    return (
        AnomalyRepository.get_all(
            db=db,
            business_series_id=(
                business_series_id
            ),
            model_id=model_id,
            status=status,
            limit=limit
        )
    )


@router.get(
    "/{anomaly_id}",
    response_model=AnomalyResponse
)
def get_anomaly(
    anomaly_id: int,

    current_user=Depends(
        require_permission(
            Permissions.ANOMALIES_VIEW
        )
    ),

    db: Session = Depends(
        get_db
    )
):
    anomaly = (
        AnomalyRepository.get_by_id(
            db,
            anomaly_id
        )
    )

    if not anomaly:

        raise HTTPException(
            status_code=404,
            detail=(
                "Anomalía no encontrada"
            )
        )

    return anomaly


@router.patch(
    "/{anomaly_id}/resolve",
    response_model=(
        AnomalyStatusResponse
    )
)
def resolve_anomaly(
    anomaly_id: int,

    current_user=Depends(
        require_permission(
            Permissions.ANOMALIES_RESOLVE
        )
    ),

    db: Session = Depends(
        get_db
    )
):
    anomaly = (
        AnomalyRepository.get_by_id(
            db,
            anomaly_id
        )
    )

    if not anomaly:

        raise HTTPException(
            status_code=404,
            detail=(
                "Anomalía no encontrada"
            )
        )

    anomaly = (
        AnomalyRepository.resolve(
            db=db,
            anomaly=anomaly
        )
    )

    AuditService.log_safe(
        db=db,
        user_id=current_user.id,
        action="anomaly.resolve",
        entity="anomaly",
        entity_id=anomaly.id,
        details={
            "business_series_id": (
                anomaly.business_series_id
            ),
            "model_id": (
                anomaly.model_id
            ),
            "prediction_id": (
                anomaly.prediction_id
            ),
            "prediction_result_id": (
                anomaly.prediction_result_id
            ),
            "anomaly_type": (
                anomaly.anomaly_type
            ),
            "severity": (
                anomaly.severity
            ),
            "status": (
                anomaly.status
            ),
        }
    )

    return {
        "id": (
            anomaly.id
        ),
        "status": (
            anomaly.status
        ),
        "resolved_at": (
            anomaly.resolved_at
        )
    }