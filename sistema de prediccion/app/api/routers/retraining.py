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

from app.repositories.model_repository import (
    ModelRepository,
)

from app.repositories.retraining_policy_repository import (
    RetrainingPolicyRepository,
)

from app.repositories.retraining_run_repository import (
    RetrainingRunRepository,
)

from app.schemas.retraining import (
    RetrainingCheckAndRunResponse,
    RetrainingCheckResponse,
    RetrainingExecuteRequest,
    RetrainingExecutionResponse,
    RetrainingPolicyCreateRequest,
    RetrainingPolicyDeleteResponse,
    RetrainingPolicyResponse,
    RetrainingPolicyStatusRequest,
    RetrainingPolicyUpdateRequest,
    RetrainingRunResponse,
)

from app.security.permissions import (
    Permissions,
    require_permission,
)

from app.services.audit_service import (
    AuditService,
)

from app.services.retraining_policy_service import (
    RetrainingPolicyService,
)

from app.services.retraining_service import (
    RetrainingService,
)


router = APIRouter(
    prefix="/retraining",
    tags=["retraining"]
)

service = RetrainingService()


# ==========================================
# POLICIES
# ==========================================

@router.post(
    "/policies",
    response_model=(
        RetrainingPolicyResponse
    ),
    status_code=201
)
def create_policy(
    payload: RetrainingPolicyCreateRequest,

    current_user=Depends(
        require_permission(
            Permissions.RETRAINING_MANAGE
        )
    ),

    db: Session = Depends(
        get_db
    )
):
    policy = (
        RetrainingPolicyService.create(
            db=db,
            model_id=(
                payload.model_id
            ),
            trigger_type=(
                payload.trigger_type
            ),
            metric_name=(
                payload.metric_name
            ),
            threshold=(
                payload.threshold
            ),
            is_active=(
                payload.is_active
            )
        )
    )

    AuditService.log_safe(
        db=db,
        user_id=current_user.id,
        action="retraining.policy.create",
        entity="retraining_policy",
        entity_id=policy.id,
        details={
            "model_id": (
                payload.model_id
            ),
            "trigger_type": (
                payload.trigger_type
            ),
            "metric_name": (
                payload.metric_name
            ),
            "threshold": (
                payload.threshold
            ),
            "is_active": (
                payload.is_active
            ),
        }
    )

    return policy


@router.get(
    "/policies",
    response_model=list[
        RetrainingPolicyResponse
    ]
)
def get_policies(
    model_id: int | None = Query(
        default=None,
        gt=0
    ),

    include_inactive: bool = Query(
        default=False
    ),

    current_user=Depends(
        require_permission(
            Permissions.RETRAINING_VIEW
        )
    ),

    db: Session = Depends(
        get_db
    )
):
    if model_id is not None:

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
            RetrainingPolicyRepository
            .get_by_model(
                db=db,
                model_id=model_id,
                active_only=(
                    not include_inactive
                )
            )
        )

    return (
        RetrainingPolicyRepository
        .get_all(
            db=db,
            include_inactive=(
                include_inactive
            )
        )
    )


@router.get(
    "/policies/{policy_id}",
    response_model=(
        RetrainingPolicyResponse
    )
)
def get_policy(
    policy_id: int,

    current_user=Depends(
        require_permission(
            Permissions.RETRAINING_VIEW
        )
    ),

    db: Session = Depends(
        get_db
    )
):
    policy = (
        RetrainingPolicyRepository.get_by_id(
            db,
            policy_id
        )
    )

    if not policy:

        raise HTTPException(
            status_code=404,
            detail=(
                "Política de "
                "reentrenamiento "
                "no encontrada"
            )
        )

    return policy


@router.put(
    "/policies/{policy_id}",
    response_model=(
        RetrainingPolicyResponse
    )
)
def update_policy(
    policy_id: int,
    payload: RetrainingPolicyUpdateRequest,

    current_user=Depends(
        require_permission(
            Permissions.RETRAINING_MANAGE
        )
    ),

    db: Session = Depends(
        get_db
    )
):
    policy = (
        RetrainingPolicyService.update(
            db=db,
            policy_id=policy_id,
            trigger_type=(
                payload.trigger_type
            ),
            metric_name=(
                payload.metric_name
            ),
            threshold=(
                payload.threshold
            ),
            is_active=(
                payload.is_active
            )
        )
    )

    AuditService.log_safe(
        db=db,
        user_id=current_user.id,
        action="retraining.policy.update",
        entity="retraining_policy",
        entity_id=policy_id,
        details={
            "trigger_type": (
                payload.trigger_type
            ),
            "metric_name": (
                payload.metric_name
            ),
            "threshold": (
                payload.threshold
            ),
            "is_active": (
                payload.is_active
            ),
        }
    )

    return policy


@router.patch(
    "/policies/{policy_id}/status",
    response_model=(
        RetrainingPolicyResponse
    )
)
def update_policy_status(
    policy_id: int,
    payload: RetrainingPolicyStatusRequest,

    current_user=Depends(
        require_permission(
            Permissions.RETRAINING_MANAGE
        )
    ),

    db: Session = Depends(
        get_db
    )
):
    policy = (
        RetrainingPolicyService.set_status(
            db=db,
            policy_id=policy_id,
            is_active=(
                payload.is_active
            )
        )
    )

    AuditService.log_safe(
        db=db,
        user_id=current_user.id,
        action=(
            "retraining.policy.status.update"
        ),
        entity="retraining_policy",
        entity_id=policy_id,
        details={
            "is_active": (
                payload.is_active
            )
        }
    )

    return policy


@router.delete(
    "/policies/{policy_id}",
    response_model=(
        RetrainingPolicyDeleteResponse
    )
)
def delete_policy(
    policy_id: int,

    current_user=Depends(
        require_permission(
            Permissions.RETRAINING_MANAGE
        )
    ),

    db: Session = Depends(
        get_db
    )
):
    policy = (
        RetrainingPolicyRepository.get_by_id(
            db,
            policy_id
        )
    )

    details = None

    if policy:

        details = {
            "model_id": (
                policy.model_id
            ),
            "trigger_type": (
                policy.trigger_type
            ),
            "metric_name": (
                policy.metric_name
            ),
            "threshold": (
                policy.threshold
            ),
        }

    RetrainingPolicyService.delete(
        db=db,
        policy_id=policy_id
    )

    AuditService.log_safe(
        db=db,
        user_id=current_user.id,
        action="retraining.policy.delete",
        entity="retraining_policy",
        entity_id=policy_id,
        details=details
    )

    return {
        "message": (
            "Política eliminada "
            "correctamente"
        )
    }


# ==========================================
# CHECK
# ==========================================

@router.get(
    "/models/{model_id}/check",
    response_model=(
        RetrainingCheckResponse
    )
)
def check_retraining(
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

    current_user=Depends(
        require_permission(
            Permissions.RETRAINING_VIEW
        )
    ),

    db: Session = Depends(
        get_db
    )
):
    return (
        service.check_model(
            db=db,
            model_id=model_id,
            limit=limit,
            minimum_observations=(
                minimum_observations
            )
        )
    )


# ==========================================
# MANUAL RETRAINING
# ==========================================

@router.post(
    "/models/{model_id}/run",
    response_model=(
        RetrainingExecutionResponse
    )
)
def run_retraining(
    model_id: int,
    payload: RetrainingExecuteRequest,

    current_user=Depends(
        require_permission(
            Permissions.RETRAINING_MANAGE
        )
    ),

    db: Session = Depends(
        get_db
    )
):
    reason = (
        payload.reason
        or (
            "Reentrenamiento iniciado "
            "manualmente"
        )
    )

    result = (
        service.execute_retraining(
            db=db,
            model_id=model_id,
            user_id=current_user.id,
            trigger_type="manual",
            reason=reason,
            dataset_id=(
                payload.dataset_id
            )
        )
    )

    run = (
        result.get(
            "run"
        )
    )

    AuditService.log_safe(
        db=db,
        user_id=current_user.id,
        action="retraining.run",
        entity="retraining_run",
        entity_id=(
            run.id
            if run
            else None
        ),
        details={
            "model_id": (
                model_id
            ),
            "dataset_id": (
                result.get(
                    "dataset_id"
                )
            ),
            "business_series_id": (
                result.get(
                    "business_series_id"
                )
            ),
            "trigger_type": (
                "manual"
            ),
            "reason": (
                reason
            ),
            "previous_version_id": (
                result.get(
                    "previous_version_id"
                )
            ),
            "new_version_id": (
                result.get(
                    "new_version_id"
                )
            ),
            "activation_required": (
                result.get(
                    "activation_required"
                )
            ),
        }
    )

    return result


# ==========================================
# POLICY CHECK + RETRAIN
# ==========================================

@router.post(
    "/models/{model_id}/check-and-run",
    response_model=(
        RetrainingCheckAndRunResponse
    )
)
def check_and_run_retraining(
    model_id: int,
    payload: RetrainingExecuteRequest,

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

    current_user=Depends(
        require_permission(
            Permissions.RETRAINING_MANAGE
        )
    ),

    db: Session = Depends(
        get_db
    )
):
    result = (
        service.check_and_run(
            db=db,
            model_id=model_id,
            user_id=current_user.id,
            dataset_id=(
                payload.dataset_id
            ),
            limit=limit,
            minimum_observations=(
                minimum_observations
            )
        )
    )

    execution = (
        result.get(
            "execution"
        )
        or {}
    )

    run = (
        execution.get(
            "run"
        )
    )

    AuditService.log_safe(
        db=db,
        user_id=current_user.id,
        action="retraining.check_and_run",
        entity="model",
        entity_id=model_id,
        details={
            "model_id": (
                model_id
            ),
            "dataset_id": (
                payload.dataset_id
            ),
            "triggered": (
                result.get(
                    "triggered",
                    False
                )
            ),
            "run_id": (
                run.id
                if run
                else None
            ),
            "new_version_id": (
                execution.get(
                    "new_version_id"
                )
            ),
        }
    )

    return result


# ==========================================
# RUN HISTORY
# ==========================================

@router.get(
    "/runs",
    response_model=list[
        RetrainingRunResponse
    ]
)
def get_retraining_runs(
    model_id: int | None = Query(
        default=None,
        gt=0
    ),

    current_user=Depends(
        require_permission(
            Permissions.RETRAINING_VIEW
        )
    ),

    db: Session = Depends(
        get_db
    )
):
    if model_id is not None:

        return (
            RetrainingRunRepository
            .get_by_model(
                db=db,
                model_id=model_id
            )
        )

    return (
        RetrainingRunRepository
        .get_all(
            db
        )
    )


@router.get(
    "/runs/{run_id}",
    response_model=(
        RetrainingRunResponse
    )
)
def get_retraining_run(
    run_id: int,

    current_user=Depends(
        require_permission(
            Permissions.RETRAINING_VIEW
        )
    ),

    db: Session = Depends(
        get_db
    )
):
    run = (
        RetrainingRunRepository.get_by_id(
            db,
            run_id
        )
    )

    if not run:

        raise HTTPException(
            status_code=404,
            detail=(
                "Ejecución de "
                "reentrenamiento "
                "no encontrada"
            )
        )

    return run