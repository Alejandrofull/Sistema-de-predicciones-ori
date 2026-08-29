from typing import Literal
from pydantic import BaseModel, Field


class ExportRequest(BaseModel):
    export_format: Literal["csv", "xlsx", "json", "parquet"] = "xlsx"
    filename: str | None = None
    records: list[dict] = Field(default_factory=list)
