from datetime import (
    date,
    datetime,
)

from pydantic import (
    BaseModel,
    Field,
    field_validator,
    model_validator,
)


class InventoryObservationCreateRequest(
    BaseModel
):

    business_series_id: int = Field(
        ...,
        gt=0
    )

    observation_date: date

    phase: str

    opening_stock: float = Field(
        ...,
        ge=0
    )

    replenishment_quantity: float = Field(
        default=0.0,
        ge=0
    )

    actual_demand: float = Field(
        ...,
        ge=0
    )

    closing_stock: float | None = Field(
        default=None,
        ge=0
    )

    predicted_demand: float | None = Field(
        default=None,
        ge=0
    )

    waste_quantity: float | None = Field(default=None, ge=0)
    max_operating_stock: float | None = Field(default=None, ge=0)
    planned_quantity: float | None = Field(default=None, ge=0)
    complete_requirements: int | None = Field(default=None, ge=0)
    total_requirements: int | None = Field(default=None, ge=0)

    source_type: str = Field(
        default="manual",
        min_length=1,
        max_length=50
    )

    @model_validator(mode="after")
    def validate_requirements(self):
        if ((self.complete_requirements is None) != (self.total_requirements is None)):
            raise ValueError("Registra conjuntamente requerimientos completos y totales")
        if self.total_requirements is not None and self.complete_requirements > self.total_requirements:
            raise ValueError("Requerimientos completos no pueden superar los totales")
        return self

    @field_validator("phase")
    @classmethod
    def validate_phase(
        cls,
        value: str
    ) -> str:

        value = (
            value
            .strip()
            .lower()
        )

        if value not in {
            "pre",
            "post",
        }:

            raise ValueError(
                "phase debe ser "
                "'pre' o 'post'"
            )

        return value

    @field_validator(
        "source_type"
    )
    @classmethod
    def normalize_source_type(
        cls,
        value: str
    ) -> str:

        return (
            value
            .strip()
            .lower()
        )

    @model_validator(
        mode="after"
    )
    def calculate_closing_stock(
        self
    ):

        available = (
            self.opening_stock
            +
            self.replenishment_quantity
        )

        calculated_closing = max(
            0.0,
            available
            -
            self.actual_demand
            -
            (self.waste_quantity or 0.0)
        )

        if self.closing_stock is None:

            self.closing_stock = (
                calculated_closing
            )

        return self


class InventoryObservationBulkRequest(
    BaseModel
):

    observations: list[
        InventoryObservationCreateRequest
    ] = Field(
        ...,
        min_length=1,
        max_length=5000
    )


class InventoryObservationResponse(
    BaseModel
):

    id: int

    business_series_id: int

    user_id: int | None

    observation_date: date

    phase: str

    opening_stock: float

    replenishment_quantity: float

    actual_demand: float

    closing_stock: float

    predicted_demand: float | None

    waste_quantity: float | None
    max_operating_stock: float | None
    planned_quantity: float | None
    complete_requirements: int | None
    total_requirements: int | None

    source_type: str

    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class InventoryPhaseKPI(BaseModel):

    phase: str

    observations: int

    total_demand: float

    total_available_stock: float

    total_served_demand: float

    total_stockout_units: float

    total_overstock_units: float

    stockout_events: int

    stockout_rate_percent: float

    service_level_percent: float

    average_closing_stock: float

    average_stockout_units: float

    average_overstock_units: float

    total_waste_units: float | None = None
    rotation_ratio: float | None = None
    availability_percent: float | None = None
    total_planned_quantity: float | None = None

    forecast_mae: float | None

    forecast_mape: float | None


class InventoryImprovementKPI(
    BaseModel
):

    stockout_units_reduction_percent: (
        float | None
    )

    stockout_events_reduction_percent: (
        float | None
    )

    overstock_reduction_percent: (
        float | None
    )

    service_level_improvement_points: (
        float | None
    )

    forecast_mae_improvement_percent: (
        float | None
    )

    forecast_mape_improvement_percent: (
        float | None
    )


class InventoryComparisonResponse(
    BaseModel
):

    business_series_id: int | None

    pre: InventoryPhaseKPI

    post: InventoryPhaseKPI

    improvement: InventoryImprovementKPI


class InventoryDeleteResponse(
    BaseModel
):

    message: str