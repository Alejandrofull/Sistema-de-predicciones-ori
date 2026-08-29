from pathlib import Path
import pandas as pd
from .base_exporter import BaseExporter


class ExcelExporter(BaseExporter):
    extension = ".xlsx"

    def export(self, data: pd.DataFrame, destination: Path) -> Path:
        destination.parent.mkdir(parents=True, exist_ok=True)
        data.to_excel(destination, index=False, engine="openpyxl")
        return destination
