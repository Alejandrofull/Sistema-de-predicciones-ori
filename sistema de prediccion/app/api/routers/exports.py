from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.export.export_service import ExportService
from app.export.sources import get_source, list_sources_for_user, user_can_access_source
from app.integrations.supabase.storage_service import SupabaseStorageService
from app.repositories.export_repository import ExportRepository
from app.schemas.export import (
    ExportDownloadResponse,
    ExportPreviewRequest,
    ExportPreviewResponse,
    ExportRequest,
    ExportResponse,
    ExportSourceInfo,
)
from app.security.permissions import Permissions, require_permission
from app.services.audit_service import AuditService

router = APIRouter(prefix="/exports", tags=["exports"])

service = ExportService()
storage = SupabaseStorageService(bucket="exports")


@router.get("/sources", response_model=list[ExportSourceInfo])
def get_export_sources(
    current_user=Depends(require_permission(Permissions.EXPORTS_GENERATE)),
    db: Session = Depends(get_db),
):
    """Fuentes de datos reales que el usuario puede exportar, con sus filtros."""
    return [
        {
            "key": source.key,
            "label": source.label,
            "filters": source.get_filters_schema(db, current_user),
        }
        for source in list_sources_for_user(db, current_user)
    ]


@router.post("/preview", response_model=ExportPreviewResponse)
def preview_export(
    payload: ExportPreviewRequest,
    current_user=Depends(require_permission(Permissions.EXPORTS_GENERATE)),
    db: Session = Depends(get_db),
):
    """Muestra una previsualización de los datos reales antes de generar el archivo."""
    try:
        source = get_source(payload.source)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    _validar_acceso_a_fuente(db, current_user, source)

    dataframe = source.fetch(db=db, current_user=current_user, filters=payload.filters)

    if dataframe.empty:
        return {"columns": list(dataframe.columns), "rows": [], "total": 0}

    preview = dataframe.head(payload.limit)

    return {
        "columns": list(dataframe.columns),
        "rows": preview.to_dict(orient="records"),
        "total": len(dataframe),
    }


@router.post("", response_model=ExportDownloadResponse)
def create_export(
    payload: ExportRequest,
    current_user=Depends(require_permission(Permissions.EXPORTS_GENERATE)),
    db: Session = Depends(get_db),
):
    try:
        source = get_source(payload.source)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    _validar_acceso_a_fuente(db, current_user, source)

    dataframe = source.fetch(db=db, current_user=current_user, filters=payload.filters)

    if dataframe.empty:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No hay registros para exportar con esos filtros",
        )

    with TemporaryDirectory() as tmp_dir:
        temporary_directory = Path(tmp_dir)

        try:
            path = service.export_dataframe(
                dataframe=dataframe,
                export_format=payload.export_format,
                filename=payload.filename,
                base_dir=temporary_directory,
            )

            remote_path = f"user_{current_user.id}/{uuid4()}_{path.name}"

            storage.upload_file(local_path=path, remote_path=remote_path)

            export = ExportRepository.create(
                db=db,
                user_id=current_user.id,
                filename=path.name,
                export_format=payload.export_format,
                storage_path=remote_path,
                status="completed",
            )

            download_url = storage.create_signed_url(remote_path=remote_path, expires_in=3600)

            AuditService.log_safe(
                db=db,
                user_id=current_user.id,
                action="export.generate",
                entity="export",
                entity_id=export.id,
                details={
                    "filename": export.filename,
                    "export_format": payload.export_format,
                    "source": payload.source,
                    "filters": payload.filters,
                    "record_count": int(len(dataframe)),
                    "storage_path": remote_path,
                },
            )

            return {
                "id": export.id,
                "filename": export.filename,
                "download_url": download_url,
                "expires_in": 3600,
            }

        except HTTPException:
            raise

        except Exception as error:
            raise HTTPException(
                status_code=500,
                detail=f"Error generando la exportación: {error}",
            )


@router.get("", response_model=list[ExportResponse])
def get_exports(
    current_user=Depends(require_permission(Permissions.EXPORTS_VIEW)),
    db: Session = Depends(get_db),
):
    return ExportRepository.get_by_user(db=db, user_id=current_user.id)


@router.get("/{export_id}/download", response_model=ExportDownloadResponse)
def download_export(
    export_id: int,
    current_user=Depends(require_permission(Permissions.EXPORTS_VIEW)),
    db: Session = Depends(get_db),
):
    export = ExportRepository.get_by_id(db=db, export_id=export_id)

    if not export:
        raise HTTPException(status_code=404, detail="Exportación no encontrada")

    if export.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tiene acceso a esta exportación")

    download_url = storage.create_signed_url(remote_path=export.storage_path, expires_in=3600)

    return {
        "id": export.id,
        "filename": export.filename,
        "download_url": download_url,
        "expires_in": 3600,
    }


@router.delete("/{export_id}")
def delete_export(
    export_id: int,
    current_user=Depends(require_permission(Permissions.EXPORTS_GENERATE)),
    db: Session = Depends(get_db),
):
    export = ExportRepository.get_by_id(db=db, export_id=export_id)

    if not export:
        raise HTTPException(status_code=404, detail="Exportación no encontrada")

    if export.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tiene acceso a esta exportación")

    filename = export.filename
    export_format = export.export_format
    storage_path = export.storage_path

    storage.remove_file(export.storage_path)
    ExportRepository.delete(db=db, export=export)

    AuditService.log_safe(
        db=db,
        user_id=current_user.id,
        action="export.delete",
        entity="export",
        entity_id=export_id,
        details={
            "filename": filename,
            "export_format": export_format,
            "storage_path": storage_path,
        },
    )

    return {"message": "Exportación eliminada correctamente"}


def _validar_acceso_a_fuente(db: Session, current_user, source) -> None:
    if not user_can_access_source(db, current_user, source):
        raise HTTPException(
            status_code=403,
            detail="No tiene permiso para exportar esta fuente de datos",
        )