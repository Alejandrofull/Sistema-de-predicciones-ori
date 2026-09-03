from __future__ import annotations

from collections.abc import Callable

from fastapi import (
    Depends,
    HTTPException,
    status,
)

from sqlalchemy.orm import Session

from app.database.session import (
    get_db,
)

from app.security.dependencies import (
    get_current_user,
)

from app.services.authorization_service import (
    AuthorizationService,
)


class Permissions:

    # ==========================================
    # USERS
    # ==========================================

    USERS_MANAGE = "users.manage"
    USERS_VIEW = "users.view"

    # ==========================================
    # ROLES
    # ==========================================

    ROLES_ASSIGN = "roles.assign"

    # ==========================================
    # DATASETS
    # ==========================================

    DATASETS_IMPORT = "datasets.import"
    DATASETS_VIEW = "datasets.view"
    DATASETS_PROCESS = "datasets.process"
    DATASETS_DELETE = "datasets.delete"

    # ==========================================
    # BUSINESS SERIES
    # ==========================================

    BUSINESS_SERIES_VIEW = (
        "business_series.view"
    )

    BUSINESS_SERIES_MANAGE = (
        "business_series.manage"
    )

    # ==========================================
    # MODELS
    # ==========================================

    MODELS_VIEW = "models.view"
    MODELS_TRAIN = "models.train"
    MODELS_EVALUATE = "models.evaluate"
    MODELS_COMPARE = "models.compare"
    MODELS_ACTIVATE = "models.activate"

    # ==========================================
    # RETRAINING
    # ==========================================

    RETRAINING_VIEW = "retraining.view"

    RETRAINING_MANAGE = (
        "retraining.manage"
    )

    # ==========================================
    # PREDICTIONS
    # ==========================================

    PREDICTIONS_RUN = "predictions.run"
    PREDICTIONS_VIEW = "predictions.view"

    # ==========================================
    # INVENTORY
    # ==========================================

    INVENTORY_VIEW = (
        "inventory.view"
    )

    INVENTORY_MANAGE = (
        "inventory.manage"
    )

    INVENTORY_IMPORT = (
        "inventory.import"
    )

    # ==========================================
    # STATISTICS
    # ==========================================

    STATISTICS_VIEW = (
        "statistics.view"
    )

    STATISTICS_RUN = (
        "statistics.run"
    )

    # ==========================================
    # KPIS
    # ==========================================

    KPIS_TECHNICAL_VIEW = (
        "kpis.technical.view"
    )

    KPIS_OPERATIONAL_VIEW = (
        "kpis.operational.view"
    )

    # ==========================================
    # REPORTS
    # ==========================================

    REPORTS_VIEW = "reports.view"

    REPORTS_GENERATE = (
        "reports.generate"
    )

    # ==========================================
    # EXPORTS
    # ==========================================

    EXPORTS_VIEW = (
        "exports.view"
    )

    EXPORTS_GENERATE = (
        "exports.generate"
    )

    # ==========================================
    # NOTIFICATIONS
    # ==========================================

    NOTIFICATIONS_VIEW = (
        "notifications.view"
    )

    NOTIFICATIONS_ACKNOWLEDGE = (
        "notifications.acknowledge"
    )

    # ==========================================
    # EXTERNAL VARIABLES
    # ==========================================

    EXTERNAL_VARIABLES_VIEW = (
        "external_variables.view"
    )

    EXTERNAL_VARIABLES_MANAGE = (
        "external_variables.manage"
    )

    # ==========================================
    # MONITORING / DRIFT
    # ==========================================

    DRIFT_VIEW = "drift.view"

    # ==========================================
    # ANOMALIES
    # ==========================================

    ANOMALIES_VIEW = "anomalies.view"
    ANOMALIES_SCAN = "anomalies.scan"

    ANOMALIES_RESOLVE = (
        "anomalies.resolve"
    )

    # ==========================================
    # AUDIT
    # ==========================================

    AUDIT_VIEW = "audit.view"


# ==========================================
# REQUIRE ONE PERMISSION
# ==========================================

def require_permission(
    permission_code: str
) -> Callable:

    def dependency(
        current_user=Depends(
            get_current_user
        ),
        db: Session = Depends(
            get_db
        )
    ):

        has_permission = (
            AuthorizationService
            .has_permission(
                db=db,
                user_id=current_user.id,
                permission_code=(
                    permission_code
                )
            )
        )

        if not has_permission:

            raise HTTPException(
                status_code=(
                    status.HTTP_403_FORBIDDEN
                ),
                detail=(
                    "No tiene permiso para "
                    "realizar esta acción"
                )
            )

        return current_user

    return dependency


# ==========================================
# REQUIRE ANY PERMISSION
# ==========================================

def require_any_permission(
    *permission_codes: str
) -> Callable:

    def dependency(
        current_user=Depends(
            get_current_user
        ),
        db: Session = Depends(
            get_db
        )
    ):

        has_permission = (
            AuthorizationService
            .has_any_permission(
                db=db,
                user_id=current_user.id,
                permission_codes=list(
                    permission_codes
                )
            )
        )

        if not has_permission:

            raise HTTPException(
                status_code=(
                    status.HTTP_403_FORBIDDEN
                ),
                detail=(
                    "No tiene ninguno de los "
                    "permisos requeridos"
                )
            )

        return current_user

    return dependency


# ==========================================
# REQUIRE ALL PERMISSIONS
# ==========================================

def require_all_permissions(
    *permission_codes: str
) -> Callable:

    def dependency(
        current_user=Depends(
            get_current_user
        ),
        db: Session = Depends(
            get_db
        )
    ):

        has_permission = (
            AuthorizationService
            .has_all_permissions(
                db=db,
                user_id=current_user.id,
                permission_codes=list(
                    permission_codes
                )
            )
        )

        if not has_permission:

            raise HTTPException(
                status_code=(
                    status.HTTP_403_FORBIDDEN
                ),
                detail=(
                    "No tiene todos los "
                    "permisos requeridos"
                )
            )

        return current_user

    return dependency