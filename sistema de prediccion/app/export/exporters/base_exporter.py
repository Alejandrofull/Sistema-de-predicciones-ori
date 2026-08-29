from abc import ABC, abstractmethod
from pathlib import Path
import pandas as pd


class BaseExporter(ABC):
    extension: str

    @abstractmethod
    def export(self, data: pd.DataFrame, destination: Path) -> Path:
        """Export a normalized DataFrame to destination and return the file path."""
        raise NotImplementedError
