from datetime import date

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

from app.repositories.inventory_observation_repository import (
    InventoryObservationRepository,
)

from app.schemas.inventory import (
    InventoryComparisonResponse,
    InventoryDeleteResponse,
    InventoryObservationBulkRequest,
    InventoryObservationCreateRequest,
    InventoryObservationResponse,
)

from app.security.permissions import (
    Permissions,
    require_permission,
)

from app.services.audit_service import (
    AuditService,
)

from app.services.inventory_kpi_service import (
    InventoryKPIService,
)


router = APIRouter(
    prefix="/inventory",
    tags=["inventory"]
)

service = InventoryKPIService()


# ==========================================
# CREAR OBSERVACIÓN
# ==========================================

@router.post(
    "/observations",
    response_model=(
        InventoryObservationResponse
    ),
    status_code=201
)
def create_inventory_observation(
    payload: InventoryObservationCreateRequest,

    current_user=Depends(
        require_permission(
            Permissions.INVENTORY_MANAGE
        )
    ),

    db: Session = Depends(
        get_db
    )
):
    observation = (
        service.create_observation(
            db=db,
            user_id=current_user.id,
            business_series_id=(
                payload.business_series_id
            ),
            observation_date=(
                payload.observation_date
            ),
            phase=payload.phase,
            opening_stock=(
                payload.opening_stock
            ),
            replenishment_quantity=(
                payload.replenishment_quantity
            ),
            actual_demand=(
                payload.actual_demand
            ),
            closing_stock=float(
                payload.closing_stock
            ),
            predicted_demand=(
                payload.predicted_demand
            ),
            source_type=(
                payload.source_type
            )
        )
    )

    AuditService.log_safe(
        db=db,
        user_id=current_user.id,
        action=(
            "inventory.observation.create"
        ),
        entity="inventory_observation",
        entity_id=observation.id,
        details={
            "business_series_id": (
                observation
                .business_series_id
            ),
            "observation_date": (
                observation
                .observation_date
            ),
            "phase": (
                observation.phase
            )
        }
    )

    return observation


# ==========================================
# CREAR VARIAS
# ==========================================

@router.post(
    "/observations/bulk",
    response_model=list[
        InventoryObservationResponse
    ],
    status_code=201
)
def create_inventory_observations_bulk(
    payload: InventoryObservationBulkRequest,

    current_user=Depends(
        require_permission(
            Permissions.INVENTORY_MANAGE
        )
    ),

    db: Session = Depends(
        get_db
    )
):
    created = (
        service.create_many(
            db=db,
            user_id=current_user.id,
            observations=(
                payload.observations
            )
        )
    )

    AuditService.log_safe(
        db=db,
        user_id=current_user.id,
        action=(
            "inventory.observation.bulk_create"
        ),
        entity="inventory_observation",
        entity_id=None,
        details={
            "created_count": (
                len(
                    created
                )
            )
        }
    )

    return created


# ==========================================
# LISTAR
# ==========================================

@router.get(
    "/observations",
    response_model=list[
        InventoryObservationResponse
    ]
)
def get_inventory_observations(
    phase: str | None = Query(
        default=None
    ),

    business_series_id: int | None = Query(
        default=None,
        gt=0
    ),

    start_date: date | None = Query(
        default=None
    ),

    end_date: date | None = Query(
        default=None
    ),

    limit: int = Query(
        default=1000,
        ge=1,
        le=10000
    ),

    current_user=Depends(
        require_permission(
            Permissions.INVENTORY_VIEW
        )
    ),

    db: Session = Depends(
        get_db
    )
):
    if phase is not None:

        phase = (
            phase
            .strip()
            .lower()
        )

        if phase not in {
            "pre",
            "post",
        }:

            raise HTTPException(
                status_code=400,
                detail=(
                    "phase debe ser "
                    "'pre' o 'post'"
                )
            )

    return (
        InventoryObservationRepository
        .get_all(
            db=db,
            phase=phase,
            business_series_id=(
                business_series_id
            ),
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
    )


# ==========================================
# COMPARACIÓN PRE VS POST
# ==========================================

@router.get(
    "/kpis/comparison",
    response_model=(
        InventoryComparisonResponse
    )
)
def compare_inventory_kpis(
    business_series_id: int | None = Query(
        default=None,
        gt=0
    ),

    start_date: date | None = Query(
        default=None
    ),

    end_date: date | None = Query(
        default=None
    ),

    current_user=Depends(
        require_permission(
            Permissions.KPIS_OPERATIONAL_VIEW
        )
    ),

    db: Session = Depends(
        get_db
    )
):
    if (
        start_date is not None
        and end_date is not None
        and start_date > end_date
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "start_date no puede ser "
                "posterior a end_date"
            )
        )

    return (
        service.compare(
            db=db,
            business_series_id=(
                business_series_id
            ),
            start_date=start_date,
            end_date=end_date
        )
    )


# ==========================================
# ELIMINAR OBSERVACIÓN
# ==========================================

@router.delete(
    "/observations/{observation_id}",
    response_model=(
        InventoryDeleteResponse
    )
)
def delete_inventory_observation(
    observation_id: int,

    current_user=Depends(
        require_permission(
            Permissions.INVENTORY_MANAGE
        )
    ),

    db: Session = Depends(
        get_db
    )
):
    observation = (
        InventoryObservationRepository
        .get_by_id(
            db,
            observation_id
        )
    )

    if not observation:

        raise HTTPException(
            status_code=404,
            detail=(
                "Observación de inventario "
                "no encontrada"
            )
        )

    details = {
        "business_series_id": (
            observation.business_series_id
        ),
        "observation_date": (
            observation.observation_date
        ),
        "phase": (
            observation.phase
        )
    }

    InventoryObservationRepository.delete(
        db=db,
        observation=observation
    )

    AuditService.log_safe(
        db=db,
        user_id=current_user.id,
        action=(
            "inventory.observation.delete"
        ),
        entity="inventory_observation",
        entity_id=observation_id,
        details=details
    )

    return {
        "message": (
            "Observación eliminada "
            "correctamente"
        )
    }