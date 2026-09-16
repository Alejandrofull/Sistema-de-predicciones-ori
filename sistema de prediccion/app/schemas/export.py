from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


class ExportRequest(BaseModel):
    source: str = Field(
        ...,
        description="Clave de la fuente de datos a exportar (ej: 'usuarios', 'ventas')"
    )

    filters: dict[str, Any] = Field(
        default_factory=dict,
        description="Filtros específicos de la fuente elegida"
    )

    export_format: str = Field(
        ...,
        description="Formato de exportación: csv, xlsx o json"
    )

    filename: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Nombre del archivo sin extensión"
    )

    @field_validator("export_format")
    @classmethod
    def validate_export_format(cls, value: str) -> str:
        value = value.lower().strip()

        allowed_formats = {"csv", "xlsx", "excel", "json"}

        if value not in allowed_formats:
            raise ValueError(
                "Formato de exportación no soportado. Use: csv, xlsx o json."
            )

        if value == "excel":
            return "xlsx"

        return value

    @field_validator("filename")
    @classmethod
    def validate_filename(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("El nombre del archivo no puede estar vacío")

        forbidden_characters = {"/", "\\", ":", "*", "?", '"', "<", ">", "|"}

        if any(character in value for character in forbidden_characters):
            raise ValueError("El nombre del archivo contiene caracteres no permitidos")

        lower_value = value.lower()
        for extension in (".csv", ".xlsx", ".xls", ".json"):
            if lower_value.endswith(extension):
                value = value[: -len(extension)]
                break

        if not value.strip():
            raise ValueError("El nombre del archivo no es válido")

        return value.strip()


class ExportPreviewRequest(BaseModel):
    source: str
    filters: dict[str, Any] = Field(default_factory=dict)
    limit: int = Field(default=20, ge=1, le=200)


class ExportPreviewResponse(BaseModel):
    columns: list[str]
    rows: list[dict[str, Any]]
    total: int


class ExportSourceInfo(BaseModel):
    key: str
    label: str
    filters: list[dict[str, Any]]


class ExportResponse(BaseModel):
    id: int
    user_id: int
    filename: str
    export_format: str
    storage_path: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ExportDownloadResponse(BaseModel):
    id: int
    filename: str
    download_url: str
    expires_in: int


class ExportDeleteResponse(BaseModel):
    message: str


class ExportListResponse(BaseModel):
    exports: list[ExportResponse]
    total: int