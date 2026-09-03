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

from app.schemas.kpi import (
    OperationalKPIResponse,
    TechnicalDashboardResponse,
    TechnicalKPIResponse,
)

from app.security.permissions import (
    Permissions,
    require_permission,
)

from app.services.kpi_service import (
    KPIService,
)


router = APIRouter(
    prefix="/kpis",
    tags=["kpis"]
)

service = KPIService()


# ==========================================
# DASHBOARD TÉCNICO GENERAL
# ==========================================

@router.get(
    "/technical",
    response_model=(
        TechnicalDashboardResponse
    )
)
def get_technical_dashboard(
    current_user=Depends(
        require_permission(
            Permissions.KPIS_TECHNICAL_VIEW
        )
    ),

    db: Session = Depends(
        get_db
    )
):

    return (
        service.get_technical_dashboard(
            db=db
        )
    )


# ==========================================
# KPI TÉCNICO POR MODELO
# ==========================================

@router.get(
    "/technical/models/{model_id}",
    response_model=(
        TechnicalKPIResponse
    )
)
def get_model_technical_kpi(
    model_id: int,

    current_user=Depends(
        require_permission(
            Permissions.KPIS_TECHNICAL_VIEW
        )
    ),

    db: Session = Depends(
        get_db
    )
):

    try:

        return (
            service
            .get_model_technical_kpis(
                db=db,
                model_id=model_id
            )
        )

    except ValueError as error:

        raise HTTPException(
            status_code=404,
            detail=str(
                error
            )
        )


# ==========================================
# KPI OPERACIONAL
# ==========================================

@router.get(
    "/operational",
    response_model=(
        OperationalKPIResponse
    )
)
def get_operational_kpis(
    start_date: date | None = Query(
        default=None
    ),

    end_date: date | None = Query(
        default=None
    ),

    business_series_id: int | None = Query(
        default=None,
        gt=0
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
        service.get_operational_kpis(
            db=db,
            start_date=start_date,
            end_date=end_date,
            business_series_id=(
                business_series_id
            )
        )
    )