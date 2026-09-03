from datetime import datetime
from typing import Any

from pydantic import (
    BaseModel,
    Field,
    field_validator,
)


# ==========================================
# REPORTE GENÉRICO
# ==========================================

class ReportRequest(BaseModel):

    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description=(
            "Título principal del reporte"
        )
    )

    report_format: str = Field(
        default="pdf",
        description=(
            "Formato del reporte"
        )
    )

    filename: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description=(
            "Nombre del archivo "
            "sin extensión"
        )
    )

    report_type: str = Field(
        default="general",
        description=(
            "Tipo de reporte: general, "
            "prediction, model_evaluation, "
            "inventory, training, etc."
        )
    )

    description: str | None = Field(
        default=None,
        description=(
            "Descripción opcional "
            "del reporte"
        )
    )

    data: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Datos principales del reporte"
        )
    )

    records: list[
        dict[str, Any]
    ] = Field(
        default_factory=list,
        description=(
            "Registros tabulares "
            "del reporte"
        )
    )

    metrics: dict[
        str,
        Any
    ] = Field(
        default_factory=dict,
        description=(
            "Métricas asociadas "
            "al reporte"
        )
    )

    metadata: dict[
        str,
        Any
    ] = Field(
        default_factory=dict,
        description=(
            "Metadatos adicionales"
        )
    )

    @field_validator(
        "report_format"
    )
    @classmethod
    def validate_report_format(
        cls,
        value: str
    ) -> str:

        value = (
            value
            .lower()
            .strip()
        )

        allowed_formats = {
            "pdf",
            "html",
            "json",
        }

        if (
            value
            not in allowed_formats
        ):

            raise ValueError(
                "Formato de reporte "
                "no soportado. "
                "Use: pdf, html o json."
            )

        return value

    @field_validator(
        "filename"
    )
    @classmethod
    def validate_filename(
        cls,
        value: str
    ) -> str:

        return (
            _normalize_filename(
                value
            )
        )

    @field_validator(
        "report_type"
    )
    @classmethod
    def normalize_report_type(
        cls,
        value: str
    ) -> str:

        value = (
            value
            .lower()
            .strip()
        )

        if not value:

            return "general"

        return value


# ==========================================
# REPORTE DE RESULTADOS DE TESIS
# ==========================================

class ThesisResultsReportRequest(
    BaseModel
):

    business_series_id: int = Field(
        ...,
        gt=0
    )

    report_format: str = Field(
        default="pdf"
    )

    filename: str | None = Field(
        default=None,
        max_length=200
    )

    include_predictions: bool = Field(
        default=True
    )

    include_inventory: bool = Field(
        default=True
    )

    include_statistics: bool = Field(
        default=True
    )

    include_anomalies: bool = Field(
        default=True
    )

    prediction_limit: int = Field(
        default=50,
        ge=1,
        le=500
    )

    anomaly_limit: int = Field(
        default=50,
        ge=1,
        le=500
    )

    alpha: float = Field(
        default=0.05,
        gt=0.0,
        lt=1.0
    )

    statistical_indicators: list[
        str
    ] = Field(
        default_factory=lambda: [
            "stockout_units",
            "overstock_units",
            "service_level",
            "closing_stock",
            "forecast_absolute_error",
            "forecast_ape",
        ]
    )

    @field_validator(
        "report_format"
    )
    @classmethod
    def validate_report_format(
        cls,
        value: str
    ) -> str:

        value = (
            value
            .lower()
            .strip()
        )

        if value not in {
            "pdf",
            "html",
            "json",
        }:

            raise ValueError(
                "Formato no soportado. "
                "Use pdf, html o json."
            )

        return value

    @field_validator(
        "filename"
    )
    @classmethod
    def validate_optional_filename(
        cls,
        value: str | None
    ) -> str | None:

        if value is None:

            return None

        return (
            _normalize_filename(
                value
            )
        )

    @field_validator(
        "statistical_indicators"
    )
    @classmethod
    def validate_indicators(
        cls,
        values: list[str]
    ) -> list[str]:

        allowed = {
            "stockout_units",
            "overstock_units",
            "service_level",
            "closing_stock",
            "forecast_absolute_error",
            "forecast_ape",
        }

        normalized = []

        for value in values:

            item = (
                str(
                    value
                )
                .strip()
                .lower()
            )

            if item not in allowed:

                raise ValueError(
                    "Indicador estadístico "
                    "no soportado: "
                    f"{item}"
                )

            if item not in normalized:

                normalized.append(
                    item
                )

        if not normalized:

            raise ValueError(
                "Debe seleccionar al menos "
                "un indicador estadístico"
            )

        return normalized


# ==========================================
# RESPUESTAS
# ==========================================

class ReportResponse(BaseModel):

    id: int

    user_id: int

    filename: str

    report_format: str

    storage_path: str

    status: str

    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class ReportDownloadResponse(
    BaseModel
):

    id: int

    filename: str

    download_url: str

    expires_in: int


class ReportDeleteResponse(
    BaseModel
):

    message: str


class ReportListResponse(
    BaseModel
):

    reports: list[
        ReportResponse
    ]

    total: int


# ==========================================
# HELPER FILENAME
# ==========================================

def _normalize_filename(
    value: str
) -> str:

    value = (
        value.strip()
    )

    if not value:

        raise ValueError(
            "El nombre del archivo "
            "no puede estar vacío"
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
        "|",
    }

    if any(
        character in value
        for character
        in forbidden_characters
    ):

        raise ValueError(
            "El nombre del archivo "
            "contiene caracteres "
            "no permitidos"
        )

    lower_value = (
        value.lower()
    )

    for extension in (
        ".pdf",
        ".html",
        ".json",
    ):

        if lower_value.endswith(
            extension
        ):

            value = (
                value[
                    :-len(
                        extension
                    )
                ]
            )

            break

    value = (
        value.strip()
    )

    if not value:

        raise ValueError(
            "El nombre del archivo "
            "no es válido"
        )

    return value