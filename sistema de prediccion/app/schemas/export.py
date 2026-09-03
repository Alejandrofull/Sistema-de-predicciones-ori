from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


class ExportRequest(BaseModel):
    records: list[dict[str, Any]] = Field(
        ...,
        min_length=1,
        description="Registros que serán exportados"
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
    def validate_export_format(
        cls,
        value: str
    ) -> str:
        value = value.lower().strip()

        allowed_formats = {
            "csv",
            "xlsx",
            "excel",
            "json"
        }

        if value not in allowed_formats:
            raise ValueError(
                "Formato de exportación no soportado. "
                "Use: csv, xlsx o json."
            )

        if value == "excel":
            return "xlsx"

        return value

    @field_validator("filename")
    @classmethod
    def validate_filename(
        cls,
        value: str
    ) -> str:
        value = value.strip()

        if not value:
            raise ValueError(
                "El nombre del archivo no puede estar vacío"
            )

        forbidden_characters = {
            "/",
            "\\",
            ":",
            "*",
            "?",
            '"',
            "<",
            ">",
            "|"
        }

        if any(
            character in value
            for character in forbidden_characters
        ):
            raise ValueError(
                "El nombre del archivo contiene "
                "caracteres no permitidos"
            )

        # Quitar extensión en caso de que
        # el usuario la escriba manualmente
        lower_value = value.lower()

        for extension in (
            ".csv",
            ".xlsx",
            ".xls",
            ".json"
        ):
            if lower_value.endswith(extension):
                value = value[
                    :-len(extension)
                ]
                break

        if not value.strip():
            raise ValueError(
                "El nombre del archivo no es válido"
            )

        return value.strip()


class ExportResponse(BaseModel):
    id: int

    user_id: int

    filename: str

    export_format: str

    storage_path: str

    status: str

    created_at: datetime

    model_config = {
        "from_attributes": True
    }


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