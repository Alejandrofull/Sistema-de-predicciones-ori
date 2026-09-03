from __future__ import annotations

from pydantic import (
    BaseModel,
    Field,
)


class InventoryImportOptions(BaseModel):

    phase: str = Field(
        ...,
        pattern="^(pre|post)$"
    )

    business_series_id: int | None = Field(
        default=None,
        gt=0
    )

    date_column: str = "fecha"

    entity_column: str | None = (
        "producto"
    )

    opening_stock_column: str = (
        "stock_inicial"
    )

    replenishment_column: str = (
        "reposicion"
    )

    actual_demand_column: str = (
        "demanda_real"
    )

    closing_stock_column: str | None = (
        "stock_final"
    )

    predicted_demand_column: str | None = (
        None
    )

    source_type: str = "import"

    auto_match_prediction: bool = True

    sync_actual_values: bool = True


class InventoryImportRowError(BaseModel):

    row_number: int

    message: str

    raw_data: dict


class InventoryImportResponse(BaseModel):

    filename: str

    phase: str

    total_rows: int

    imported_rows: int

    skipped_rows: int

    matched_predictions: int

    actual_values_synced: int

    actual_values_unmatched: int

    calculated_closing_stock: int

    errors: list[
        InventoryImportRowError
    ]

    created_observation_ids: list[int]