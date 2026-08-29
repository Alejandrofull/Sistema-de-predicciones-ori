from pathlib import Path
from typing import Any
import pandas as pd
from .base_loader import BaseLoader

class JSONLoader(BaseLoader):
    def load(self, source: str | Path | list[dict[str, Any]] | dict[str, Any], **kwargs) -> pd.DataFrame:
        if isinstance(source, (str, Path)):
            return pd.read_json(source, **kwargs)
        if isinstance(source, dict):
            source = source.get("data", source)
            if isinstance(source, dict):
                source = [source]
        return pd.DataFrame(source)
