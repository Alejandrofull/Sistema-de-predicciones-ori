from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

import pandas as pd

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from sqlalchemy.orm import Session

from app.database.session import (
    get_db,
)

from app.export.export_service import (
    ExportService,
)

from app.integrations.supabase.storage_service import (
    SupabaseStorageService,
)

from app.repositories.export_repository import (
    ExportRepository,
)

from app.schemas.export import (
    ExportDownloadResponse,
    ExportRequest,
    ExportResponse,
)

from app.security.permissions import (
    Permissions,
    require_permission,
)

from app.services.audit_service import (
    AuditService,
)


router = APIRouter(
    prefix="/exports",
    tags=["exports"]
)

service = ExportService()

storage = SupabaseStorageService(
    bucket="exports"
)


@router.post(
    "",
    response_model=ExportDownloadResponse
)
def create_export(
    payload: ExportRequest,

    current_user=Depends(
        require_permission(
            Permissions.EXPORTS_GENERATE
        )
    ),

    db: Session = Depends(
        get_db
    )
):
    dataframe = pd.DataFrame(
        payload.records
    )

    if dataframe.empty:

        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=(
                "No hay registros "
                "para exportar"
            )
        )

    with TemporaryDirectory() as tmp_dir:

        temporary_directory = Path(
            tmp_dir
        )

        try:

            path = service.export_dataframe(
                dataframe=dataframe,
                export_format=(
                    payload.export_format
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

            export = ExportRepository.create(
                db=db,
                user_id=current_user.id,
                filename=path.name,
                export_format=(
                    payload.export_format
                ),
                storage_path=remote_path,
                status="completed"
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
                action="export.generate",
                entity="export",
                entity_id=export.id,
                details={
                    "filename": (
                        export.filename
                    ),
                    "export_format": (
                        payload.export_format
                    ),
                    "record_count": int(
                        len(
                            dataframe
                        )
                    ),
                    "storage_path": (
                        remote_path
                    ),
                }
            )

            return {
                "id": export.id,
                "filename": (
                    export.filename
                ),
                "download_url": (
                    download_url
                ),
                "expires_in": 3600
            }

        except HTTPException:
            raise

        except Exception as error:

            raise HTTPException(
                status_code=500,
                detail=(
                    "Error generando "
                    "la exportación: "
                    f"{error}"
                )
            )


@router.get(
    "",
    response_model=list[
        ExportResponse
    ]
)
def get_exports(
    current_user=Depends(
        require_permission(
            Permissions.EXPORTS_VIEW
        )
    ),

    db: Session = Depends(
        get_db
    )
):
    return (
        ExportRepository.get_by_user(
            db=db,
            user_id=current_user.id
        )
    )


@router.get(
    "/{export_id}/download",
    response_model=ExportDownloadResponse
)
def download_export(
    export_id: int,

    current_user=Depends(
        require_permission(
            Permissions.EXPORTS_VIEW
        )
    ),

    db: Session = Depends(
        get_db
    )
):
    export = (
        ExportRepository.get_by_id(
            db=db,
            export_id=export_id
        )
    )

    if not export:

        raise HTTPException(
            status_code=404,
            detail=(
                "Exportación no encontrada"
            )
        )

    if export.user_id != current_user.id:

        raise HTTPException(
            status_code=403,
            detail=(
                "No tiene acceso "
                "a esta exportación"
            )
        )

    download_url = (
        storage.create_signed_url(
            remote_path=export.storage_path,
            expires_in=3600
        )
    )

    return {
        "id": export.id,
        "filename": export.filename,
        "download_url": download_url,
        "expires_in": 3600
    }


@router.delete(
    "/{export_id}"
)
def delete_export(
    export_id: int,

    current_user=Depends(
        require_permission(
            Permissions.EXPORTS_GENERATE
        )
    ),

    db: Session = Depends(
        get_db
    )
):
    export = (
        ExportRepository.get_by_id(
            db=db,
            export_id=export_id
        )
    )

    if not export:

        raise HTTPException(
            status_code=404,
            detail=(
                "Exportación no encontrada"
            )
        )

    if export.user_id != current_user.id:

        raise HTTPException(
            status_code=403,
            detail=(
                "No tiene acceso "
                "a esta exportación"
            )
        )

    filename = (
        export.filename
    )

    export_format = (
        export.export_format
    )

    storage_path = (
        export.storage_path
    )

    storage.remove_file(
        export.storage_path
    )

    ExportRepository.delete(
        db=db,
        export=export
    )

    AuditService.log_safe(
        db=db,
        user_id=current_user.id,
        action="export.delete",
        entity="export",
        entity_id=export_id,
        details={
            "filename": (
                filename
            ),
            "export_format": (
                export_format
            ),
            "storage_path": (
                storage_path
            ),
        }
    )

    return {
        "message": (
            "Exportación eliminada "
            "correctamente"
        )
    }