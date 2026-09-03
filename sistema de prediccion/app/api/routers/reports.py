from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from sqlalchemy.orm import Session

from app.database.session import (
    get_db,
)

from app.integrations.supabase.storage_service import (
    SupabaseStorageService,
)

from app.reports.report_service import (
    ReportService,
)

from app.reports.thesis_results_report import (
    ThesisResultsReport,
)

from app.repositories.report_repository import (
    ReportRepository,
)

from app.schemas.report import (
    ReportDownloadResponse,
    ReportRequest,
    ReportResponse,
    ThesisResultsReportRequest,
)

from app.security.permissions import (
    Permissions,
    require_permission,
)

from app.services.audit_service import (
    AuditService,
)

from app.services.thesis_report_service import (
    ThesisReportService,
)


router = APIRouter(
    prefix="/reports",
    tags=["reports"]
)

service = ReportService()

thesis_service = (
    ThesisReportService()
)

thesis_renderer = (
    ThesisResultsReport()
)

storage = SupabaseStorageService(
    bucket="reports"
)


# ==========================================
# REPORTE GENÉRICO
# ==========================================

@router.post(
    "",
    response_model=ReportDownloadResponse
)
def create_report(
    payload: ReportRequest,

    current_user=Depends(
        require_permission(
            Permissions.REPORTS_GENERATE
        )
    ),

    db: Session = Depends(
        get_db
    )
):
    context = (
        payload.model_dump(
            exclude={
                "report_format",
                "filename"
            }
        )
    )

    uploaded_path = None

    with TemporaryDirectory() as tmp_dir:

        temporary_directory = Path(
            tmp_dir
        )

        try:

            path = service.generate(
                context=context,
                report_format=(
                    payload.report_format
                ),
                filename=(
                    payload.filename
                ),
                base_dir=(
                    temporary_directory
                )
            )

            remote_path = (
                f"user_{current_user.id}/"
                f"{uuid4()}_{path.name}"
            )

            storage.upload_file(
                local_path=path,
                remote_path=remote_path
            )

            uploaded_path = (
                remote_path
            )

            report = (
                ReportRepository.create(
                    db=db,
                    user_id=(
                        current_user.id
                    ),
                    filename=path.name,
                    report_format=(
                        payload.report_format
                    ),
                    storage_path=(
                        remote_path
                    ),
                    status="completed"
                )
            )

            download_url = (
                storage.create_signed_url(
                    remote_path=remote_path,
                    expires_in=3600
                )
            )

            AuditService.log_safe(
                db=db,
                user_id=current_user.id,
                action="report.generate",
                entity="report",
                entity_id=report.id,
                details={
                    "report_type": (
                        payload.report_type
                    ),
                    "filename": (
                        report.filename
                    ),
                    "report_format": (
                        payload.report_format
                    ),
                    "storage_path": (
                        remote_path
                    ),
                }
            )

            return {
                "id": report.id,
                "filename": (
                    report.filename
                ),
                "download_url": (
                    download_url
                ),
                "expires_in": 3600
            }

        except HTTPException:
            raise

        except Exception as error:

            if uploaded_path:

                try:

                    storage.remove_file(
                        uploaded_path
                    )

                except Exception:
                    pass

            raise HTTPException(
                status_code=500,
                detail=(
                    "Error generando "
                    "el reporte: "
                    f"{error}"
                )
            )


# ==========================================
# REPORTE CONSOLIDADO DE TESIS
# ==========================================

@router.post(
    "/thesis-results",
    response_model=(
        ReportDownloadResponse
    )
)
def create_thesis_results_report(
    payload: ThesisResultsReportRequest,

    current_user=Depends(
        require_permission(
            Permissions.REPORTS_GENERATE
        )
    ),

    db: Session = Depends(
        get_db
    )
):
    uploaded_path = None

    try:

        # ======================================
        # CONTEXTO DIRECTO DESDE BD
        # ======================================

        context = (
            thesis_service.build_context(
                db=db,
                business_series_id=(
                    payload.business_series_id
                ),
                include_predictions=(
                    payload.include_predictions
                ),
                include_inventory=(
                    payload.include_inventory
                ),
                include_statistics=(
                    payload.include_statistics
                ),
                include_anomalies=(
                    payload.include_anomalies
                ),
                prediction_limit=(
                    payload.prediction_limit
                ),
                anomaly_limit=(
                    payload.anomaly_limit
                ),
                alpha=payload.alpha,
                statistical_indicators=(
                    payload
                    .statistical_indicators
                )
            )
        )

        # ======================================
        # FILENAME
        # ======================================

        filename = (
            payload.filename
            or (
                "reporte_resultados_tesis_"
                f"serie_{payload.business_series_id}"
            )
        )

        # ======================================
        # ARCHIVO TEMPORAL
        # ======================================

        with TemporaryDirectory() as tmp_dir:

            temporary_directory = Path(
                tmp_dir
            )

            path = (
                thesis_renderer.generate(
                    context=context,
                    report_format=(
                        payload.report_format
                    ),
                    filename=filename,
                    base_dir=(
                        temporary_directory
                    )
                )
            )

            # ==================================
            # STORAGE
            # ==================================

            remote_path = (
                f"user_{current_user.id}/"
                "thesis/"
                f"{uuid4()}_{path.name}"
            )

            storage.upload_file(
                local_path=path,
                remote_path=remote_path
            )

            uploaded_path = (
                remote_path
            )

            # ==================================
            # BD
            # ==================================

            report = (
                ReportRepository.create(
                    db=db,
                    user_id=(
                        current_user.id
                    ),
                    filename=path.name,
                    report_format=(
                        payload.report_format
                    ),
                    storage_path=(
                        remote_path
                    ),
                    status="completed"
                )
            )

        # ======================================
        # URL FIRMADA
        # ======================================

        download_url = (
            storage.create_signed_url(
                remote_path=(
                    uploaded_path
                ),
                expires_in=3600
            )
        )

        # ======================================
        # AUDITORÍA
        # ======================================

        AuditService.log_safe(
            db=db,
            user_id=current_user.id,
            action=(
                "report.thesis_results.generate"
            ),
            entity="report",
            entity_id=report.id,
            details={
                "business_series_id": (
                    payload.business_series_id
                ),
                "filename": (
                    report.filename
                ),
                "report_format": (
                    payload.report_format
                ),
                "include_predictions": (
                    payload.include_predictions
                ),
                "include_inventory": (
                    payload.include_inventory
                ),
                "include_statistics": (
                    payload.include_statistics
                ),
                "include_anomalies": (
                    payload.include_anomalies
                ),
                "alpha": (
                    payload.alpha
                ),
            }
        )

        return {
            "id": (
                report.id
            ),
            "filename": (
                report.filename
            ),
            "download_url": (
                download_url
            ),
            "expires_in": 3600
        }

    except HTTPException:
        raise

    except Exception as error:

        if uploaded_path:

            try:

                storage.remove_file(
                    uploaded_path
                )

            except Exception:
                pass

        raise HTTPException(
            status_code=500,
            detail=(
                "Error generando el "
                "reporte consolidado "
                "de tesis: "
                f"{error}"
            )
        )


# ==========================================
# LISTAR REPORTES
# ==========================================

@router.get(
    "",
    response_model=list[
        ReportResponse
    ]
)
def get_reports(
    current_user=Depends(
        require_permission(
            Permissions.REPORTS_VIEW
        )
    ),

    db: Session = Depends(
        get_db
    )
):
    return (
        ReportRepository.get_by_user(
            db=db,
            user_id=current_user.id
        )
    )


# ==========================================
# DESCARGAR
# ==========================================

@router.get(
    "/{report_id}/download",
    response_model=(
        ReportDownloadResponse
    )
)
def download_report(
    report_id: int,

    current_user=Depends(
        require_permission(
            Permissions.REPORTS_VIEW
        )
    ),

    db: Session = Depends(
        get_db
    )
):
    report = (
        ReportRepository.get_by_id(
            db=db,
            report_id=report_id
        )
    )

    if not report:

        raise HTTPException(
            status_code=404,
            detail=(
                "Reporte no encontrado"
            )
        )

    if (
        report.user_id
        != current_user.id
    ):

        raise HTTPException(
            status_code=403,
            detail=(
                "No tiene acceso "
                "a este reporte"
            )
        )

    download_url = (
        storage.create_signed_url(
            remote_path=(
                report.storage_path
            ),
            expires_in=3600
        )
    )

    return {
        "id": report.id,
        "filename": (
            report.filename
        ),
        "download_url": (
            download_url
        ),
        "expires_in": 3600
    }


# ==========================================
# ELIMINAR
# ==========================================

@router.delete(
    "/{report_id}"
)
def delete_report(
    report_id: int,

    current_user=Depends(
        require_permission(
            Permissions.REPORTS_GENERATE
        )
    ),

    db: Session = Depends(
        get_db
    )
):
    report = (
        ReportRepository.get_by_id(
            db=db,
            report_id=report_id
        )
    )

    if not report:

        raise HTTPException(
            status_code=404,
            detail=(
                "Reporte no encontrado"
            )
        )

    if (
        report.user_id
        != current_user.id
    ):

        raise HTTPException(
            status_code=403,
            detail=(
                "No tiene acceso "
                "a este reporte"
            )
        )

    filename = (
        report.filename
    )

    report_format = (
        report.report_format
    )

    storage_path = (
        report.storage_path
    )

    storage.remove_file(
        report.storage_path
    )

    ReportRepository.delete(
        db=db,
        report=report
    )

    AuditService.log_safe(
        db=db,
        user_id=current_user.id,
        action="report.delete",
        entity="report",
        entity_id=report_id,
        details={
            "filename": (
                filename
            ),
            "report_format": (
                report_format
            ),
            "storage_path": (
                storage_path
            ),
        }
    )

    return {
        "message": (
            "Reporte eliminado "
            "correctamente"
        )
    }