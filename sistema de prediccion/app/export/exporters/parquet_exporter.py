from pathlib import Path
import pandas as pd
from .base_exporter import BaseExporter


class ParquetExporter(BaseExporter):
    extension = ".parquet"

    def export(self, data: pd.DataFrame, destination: Path) -> Path:
        destination.parent.mkdir(parents=True, exist_ok=True)
        data.to_parquet(destination, index=False)
        return destination
