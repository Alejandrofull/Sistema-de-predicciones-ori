from typing import Any

from pydantic import (
    BaseModel,
    Field,
    field_validator
)


class DatasetProcessingRequest(
    BaseModel
):
    date_column: str | None = Field(
        default=None
    )

    target_column: str | None = Field(
        default=None
    )

    remove_duplicates: bool = True

    fill_missing_target: bool = True

    generate_features: bool = True

    lags: list[int] = Field(
        default_factory=lambda: [
            1,
            7,
            14,
            28
        ]
    )

    rolling_windows: list[int] = Field(
        default_factory=lambda: [
            7,
            14,
            28
        ]
    )

    @field_validator("lags")
    @classmethod
    def validate_lags(
        cls,
        values: list[int]
    ) -> list[int]:

        cleaned = sorted(
            {
                int(value)
                for value in values
                if int(value) > 0
            }
        )

        if not cleaned:
            raise ValueError(
                "Debe existir al menos un lag válido"
            )

        return cleaned

    @field_validator(
        "rolling_windows"
    )
    @classmethod
    def validate_rolling_windows(
        cls,
        values: list[int]
    ) -> list[int]:

        cleaned = sorted(
            {
                int(value)
                for value in values
                if int(value) > 1
            }
        )

        if not cleaned:
            raise ValueError(
                "Debe existir al menos "
                "una ventana móvil válida"
            )

        return cleaned


class DatasetProcessingResponse(
    BaseModel
):
    source_dataset_id: int

    processed_dataset_id: int

    name: str

    processing_stage: str

    file_format: str

    storage_path: str

    rows: int

    columns: int

    date_column: str

    target_column: str

    preprocessing_report: dict[
        str,
        Any
    ]

    feature_report: dict[
        str,
        Any
    ] | None

    preview: list[
        dict[
            str,
            Any
        ]
    ]