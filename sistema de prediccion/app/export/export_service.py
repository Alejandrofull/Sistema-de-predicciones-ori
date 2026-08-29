from pathlib import Path
from uuid import uuid4
import pandas as pd
from .export_factory import get_exporter


class ExportService:
    def __init__(self, base_dir: str = "storage/exports"):
        self.base_dir = Path(base_dir)

    def export_dataframe(self, data: pd.DataFrame, export_format: str, filename: str | None = None) -> Path:
        exporter = get_exporter(export_format)
        stem = filename or f"export_{uuid4().hex}"
        destination = self.base_dir / f"{stem}{exporter.extension}"
        return exporter.export(data, destination)
