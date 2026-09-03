from typing import Any

from pydantic import (
    BaseModel,
    Field,
    field_validator,
)


class SeriesExtractionRequest(
    BaseModel
):

    date_column: str = Field(
        ...,
        min_length=1
    )

    entity_column: str = Field(
        ...,
        min_length=1
    )

    target_column: str = Field(
        ...,
        min_length=1
    )

    entity_type: str = Field(
        default="product",
        min_length=1,
        max_length=50
    )

    aggregation: str = Field(
        default="sum"
    )

    minimum_observations: int = Field(
        default=30,
        ge=2
    )

    @field_validator(
        "date_column",
        "entity_column",
        "target_column"
    )
    @classmethod
    def normalize_column(
        cls,
        value: str
    ) -> str:

        value = value.strip()

        if not value:
            raise ValueError(
                "El nombre de columna "
                "no puede estar vacío"
            )

        return value

    @field_validator(
        "entity_type"
    )
    @classmethod
    def normalize_entity_type(
        cls,
        value: str
    ) -> str:

        value = (
            value
            .strip()
            .lower()
        )

        if not value:
            raise ValueError(
                "entity_type "
                "es obligatorio"
            )

        return value

    @field_validator(
        "aggregation"
    )
    @classmethod
    def validate_aggregation(
        cls,
        value: str
    ) -> str:

        value = (
            value
            .strip()
            .lower()
        )

        allowed = {
            "sum",
            "mean",
            "max",
            "min"
        }

        if value not in allowed:
            raise ValueError(
                "aggregation debe ser: "
                "sum, mean, max o min"
            )

        return value


class ExtractedSeriesResponse(
    BaseModel
):

    business_series_id: int

    dataset_id: int

    external_entity_id: str

    name: str

    entity_type: str

    rows: int

    date_column: str

    target_column: str

    storage_path: str


class SeriesExtractionResponse(
    BaseModel
):

    source_dataset_id: int

    entity_column: str

    entities_detected: int

    series_created: int

    series_skipped: int

    extracted_series: list[
        ExtractedSeriesResponse
    ]

    skipped_series: list[
        dict[
            str,
            Any
        ]
    ]