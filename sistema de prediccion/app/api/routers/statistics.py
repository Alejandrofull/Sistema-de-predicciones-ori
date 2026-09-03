from fastapi import (
    APIRouter,
    Depends,
)

from sqlalchemy.orm import Session

from app.database.session import (
    get_db,
)

from app.schemas.statistics import (
    InventoryStatisticalAnalysisResponse,
    StatisticalAnalysisRequest,
)

from app.security.permissions import (
    Permissions,
    require_permission,
)

from app.services.inventory_statistics_service import (
    InventoryStatisticsService,
)


router = APIRouter(
    prefix="/statistics",
    tags=["statistics"]
)

service = (
    InventoryStatisticsService()
)


@router.post(
    "/inventory/pre-post",
    response_model=(
        InventoryStatisticalAnalysisResponse
    )
)
def analyze_inventory_pre_post(
    payload: StatisticalAnalysisRequest,

    current_user=Depends(
        require_permission(
            Permissions.STATISTICS_RUN
        )
    ),

    db: Session = Depends(
        get_db
    )
):
    return (
        service.analyze(
            db=db,
            business_series_id=(
                payload.business_series_id
            ),
            indicators=(
                payload.indicators
            ),
            alpha=payload.alpha
        )
    )