from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import pandas as pd

from app.export.export_service import ExportService
from app.schemas.export import ExportRequest

router = APIRouter(prefix="/exports", tags=["exports"])
service = ExportService()


@router.post("")
def create_export(payload: ExportRequest):
    path = service.export_dataframe(pd.DataFrame(payload.records), payload.export_format, payload.filename)
    return {
        "status": "completed",
        "format": payload.export_format,
        "filename": path.name,
        "download_url": f"/api/v1/exports/{path.name}",
    }


@router.get("/{filename}")
def download_export(filename: str):
    base = service.base_dir.resolve()
    path = (base / Path(filename).name).resolve()
    if path.parent != base or not path.is_file():
        raise HTTPException(status_code=404, detail="Exportación no encontrada")
    return FileResponse(path=path, filename=path.name)
