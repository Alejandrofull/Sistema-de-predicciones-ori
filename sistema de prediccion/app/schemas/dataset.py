from datetime import datetime
from typing import Any

from pydantic import (
    BaseModel,
    Field,
)


class DatasetResponse(BaseModel):

    id: int

    user_id: int | None

    parent_dataset_id: int | None

    business_series_id: int | None

    name: str

    original_filename: str | None

    file_format: str | None

    source_type: str

    processing_stage: str

    storage_path: str | None

    row_count: int

    column_count: int

    columns_info: list[Any] | None

    quality_report: dict[
        str,
        Any
    ] | None

    dataset_metadata: dict[
        str,
        Any
    ] | None

    status: str

    created_at: datetime

    updated_at: datetime

    model_config = {
        "from_attributes": True
    }


class DatasetUploadResponse(BaseModel):

    id: int

    name: str

    original_filename: str

    file_format: str

    row_count: int

    column_count: int

    columns: list[str]

    quality_report: dict[
        str,
        Any
    ]

    storage_path: str

    status: str

    preview: list[
        dict[
            str,
            Any
        ]
    ]


class DatasetDownloadResponse(BaseModel):

    id: int

    filename: str

    download_url: str

    expires_in: int


class DatasetDeleteResponse(BaseModel):

    message: str


class DatasetStatusResponse(BaseModel):

    id: int

    status: str


class DatasetMetadataUpdate(BaseModel):

    metadata: dict[
        str,
        Any
    ] = Field(
        default_factory=dict
    )