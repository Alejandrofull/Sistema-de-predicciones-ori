from typing import Any, Literal
from pydantic import BaseModel, Field, HttpUrl

SourceType = Literal["csv", "xlsx", "xls", "json", "parquet", "database", "api"]

class DatabaseImportRequest(BaseModel):
    connection_url: str
    query: str | None = None
    table: str | None = None

class APIImportRequest(BaseModel):
    url: HttpUrl
    method: str = "GET"
    headers: dict[str, str] | None = None
    params: dict[str, Any] | None = None
    records_path: str | None = None

class DatasetPrepareRequest(BaseModel):
    date_column: str
    target_column: str
    missing_strategy: Literal["drop", "ffill", "bfill", "interpolate"] = "drop"
    numeric_features: list[str] = Field(default_factory=list)
