from pathlib import Path
import pandas as pd
from .base_exporter import BaseExporter


class CSVExporter(BaseExporter):
    extension = ".csv"

    def export(self, data: pd.DataFrame, destination: Path) -> Path:
        destination.parent.mkdir(parents=True, exist_ok=True)
        data.to_csv(destination, index=False, encoding="utf-8-sig")
        return destination
