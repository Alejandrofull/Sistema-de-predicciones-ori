from typing import Literal
from pydantic import BaseModel, Field


class ReportRequest(BaseModel):
    title: str = "Reporte de predicción"
    summary: str = ""
    report_format: Literal["pdf", "xlsx", "html"] = "pdf"
    metrics: dict = Field(default_factory=dict)
    predictions: list[dict] = Field(default_factory=list)
    filename: str | None = None
