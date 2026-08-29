from abc import ABC, abstractmethod
from typing import Any
import pandas as pd

class BaseLoader(ABC):
    """Contract for every data source used by the prediction pipeline."""

    @abstractmethod
    def load(self, source: Any, **kwargs) -> pd.DataFrame:
        raise NotImplementedError
