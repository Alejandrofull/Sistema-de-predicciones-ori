from typing import Any
import httpx
import pandas as pd
from .base_loader import BaseLoader

class APILoader(BaseLoader):
    """Loads JSON records from REST APIs."""

    def load(self, source: str, **kwargs) -> pd.DataFrame:
        method = kwargs.pop("method", "GET").upper()
        records_path = kwargs.pop("records_path", None)
        timeout = kwargs.pop("timeout", 30.0)
        with httpx.Client(timeout=timeout) as client:
            response = client.request(method, source, **kwargs)
            response.raise_for_status()
            payload: Any = response.json()
        if records_path:
            for key in records_path.split("."):
                payload = payload[key]
        if isinstance(payload, dict):
            payload = payload.get("data", payload)
            if isinstance(payload, dict):
                payload = [payload]
        return pd.DataFrame(payload)
