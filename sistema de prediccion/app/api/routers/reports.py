from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.reports.report_service import ReportService
from app.schemas.report import ReportRequest

router = APIRouter(prefix="/reports", tags=["reports"])
service = ReportService()


@router.post("")
def create_report(payload: ReportRequest):
    context = payload.model_dump(exclude={"report_format", "filename"})
    path = service.generate(context, payload.report_format, payload.filename)
    return {
        "status": "completed",
        "format": payload.report_format,
        "filename": path.name,
        "download_url": f"/api/v1/reports/{path.name}",
    }


@router.get("/{filename}")
def download_report(filename: str):
    base = service.base_dir.resolve()
    path = (base / Path(filename).name).resolve()
    if path.parent != base or not path.is_file():
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    return FileResponse(path=path, filename=path.name)
