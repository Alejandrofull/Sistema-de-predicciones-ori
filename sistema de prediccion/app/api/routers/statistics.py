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

# Segmented interrupted time-series analysis (separate from paired t/Wilcoxon).
from datetime import date as _date
from fastapi import Query, HTTPException
from sqlalchemy import select
from app.models.inventory_intervention import InventoryIntervention
from app.repositories.inventory_observation_repository import InventoryObservationRepository
from app.services.inventory_statistics_service import InventoryStatisticsService as _S

@router.get("/inventory/its")
def analyze_interrupted_time_series(
    business_series_id: int = Query(gt=0),
    indicator: str = Query(default="stockout_units"),
    current_user=Depends(require_permission(Permissions.STATISTICS_RUN)),
    db: Session = Depends(get_db),
):
    import numpy as np
    import statsmodels.api as sm
    valid = {"stockout_units", "overstock_units", "waste_units", "rotation", "availability", "planned_quantity", "service_level", "closing_stock"}
    if indicator not in valid: raise HTTPException(422, "Indicador ITS no soportado")
    cutoff = db.scalar(select(InventoryIntervention.start_date).order_by(InventoryIntervention.start_date).limit(1))
    if cutoff is None: raise HTTPException(400, "Registra primero la fecha de intervención")
    rows = InventoryObservationRepository.get_all(db, business_series_id=business_series_id, limit=100000)
    points = [(o.observation_date, _S._indicator_value(o, indicator)) for o in rows]
    points = [(d, y) for d, y in points if y is not None and np.isfinite(y)]
    points.sort(key=lambda x: x[0])
    if len(set(d for d, _ in points)) != len(points):
        raise HTTPException(422, "Se requiere una observación por fecha para ITS")
    pre_count = sum(d < cutoff for d, _ in points)
    post_count = sum(d >= cutoff for d, _ in points)
    if pre_count < 4 or post_count < 4: raise HTTPException(400, "ITS requiere al menos 4 mediciones PRE y 4 POST")
    # Actual elapsed days, not row indexes, handles irregular sampling.
    days = np.array([(d - points[0][0]).days for d, _ in points], dtype=float)
    t0 = float((cutoff - points[0][0]).days)
    post = (days >= t0).astype(float)
    matrix = np.column_stack([np.ones(len(days)), days, post, np.maximum(days - t0, 0)])
    y = np.array([v for _, v in points], dtype=float)
    if np.linalg.matrix_rank(matrix) < 4: raise HTTPException(422, "Diseño ITS no identificable")
    fit = sm.OLS(y, matrix).fit(cov_type="HAC", cov_kwds={"maxlags": min(3, len(days) // 4)})
    ci = fit.conf_int(alpha=0.05)
    return {
        "business_series_id": business_series_id, "indicator": indicator,
        "intervention_start_date": cutoff, "pre_observations": pre_count,
        "post_observations": post_count, "method": "OLS segmented regression, HAC robust SE",
        "terms": [
            {"name": name, "coefficient": float(fit.params[i]), "p_value": float(fit.pvalues[i]), "ci95": [float(v) for v in ci[i]]}
            for i, name in enumerate(["intercept", "pre_trend_per_day", "immediate_level_change", "trend_change_per_day"])
        ],
        "r_squared": float(fit.rsquared),
        "note": "Asociación temporal; la regresión por sí sola no demuestra causalidad.",
    }
