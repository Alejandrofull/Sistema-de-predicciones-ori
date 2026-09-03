from typing import Any

from pydantic import BaseModel


class DatasetValidationResponse(
    BaseModel
):
    dataset_id: int

    status: str

    is_trainable: bool

    rows: int

    columns: int

    date_column: str | None

    target_column: str | None

    frequency: str | None

    date_range: dict[
        str,
        Any
    ] | None

    duplicate_rows: int

    null_report: list[
        dict[
            str,
            Any
        ]
    ]

    numeric_columns: list[
        str
    ]

    outliers: dict[
        str,
        Any
    ]

    target_analysis: dict[
        str,
        Any
    ] | None

    issues: list[
        dict[
            str,
            Any
        ]
    ]

    summary: dict[
        str,
        int
    ]