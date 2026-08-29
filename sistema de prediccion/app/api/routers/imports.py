from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.services.import_service import ImportService

router = APIRouter(prefix="/imports", tags=["data-imports"])
service = ImportService()

ALLOWED_EXTENSIONS = {"csv", "xlsx", "xls", "json", "parquet"}


@router.get("/formats")
def supported_formats():
    return {
        "files": sorted(ALLOWED_EXTENSIONS),
        "sources": ["database", "api"],
        "pipeline": [
            "ingestion",
            "validation",
            "cleaning",
            "transformation",
            "feature_engineering",
            "prediction",
            "export",
            "reporting",
        ],
    }


@router.post("/file")
async def import_file(file: UploadFile = File(...)):
    suffix = Path(file.filename or "").suffix.lower().lstrip(".")
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=415, detail=f"Formato no soportado: {suffix or 'sin extensión'}")

    with NamedTemporaryFile(delete=False, suffix=f".{suffix}") as tmp:
        tmp.write(await file.read())
        temp_path = Path(tmp.name)

    try:
        df = service.load(suffix, temp_path)
        return {
            "filename": file.filename,
            "format": suffix,
            "rows": len(df),
            "columns": list(df.columns),
            "quality": service.quality_report(df),
            "preview": df.head(10).where(df.notna(), None).to_dict(orient="records"),
        }
    finally:
        temp_path.unlink(missing_ok=True)
