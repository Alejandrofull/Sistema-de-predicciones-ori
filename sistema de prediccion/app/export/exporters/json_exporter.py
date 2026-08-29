from pathlib import Path
import pandas as pd
from .base_exporter import BaseExporter


class JSONExporter(BaseExporter):
    extension = ".json"

    def export(self, data: pd.DataFrame, destination: Path) -> Path:
        destination.parent.mkdir(parents=True, exist_ok=True)
        data.to_json(destination, orient="records", date_format="iso", force_ascii=False, indent=2)
        return destination
