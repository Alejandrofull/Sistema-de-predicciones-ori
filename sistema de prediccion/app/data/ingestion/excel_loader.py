from pathlib import Path
import pandas as pd
from .base_loader import BaseLoader

class ExcelLoader(BaseLoader):
    def load(self, source: str | Path, **kwargs) -> pd.DataFrame:
        return pd.read_excel(source, **kwargs)
