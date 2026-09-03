from __future__ import annotations

from pydantic import (
    BaseModel,
    Field,
    field_validator,
)


class DescriptiveStatistics(BaseModel):

    count: int

    mean: float | None

    median: float | None

    standard_deviation: float | None

    variance: float | None

    minimum: float | None

    maximum: float | None

    q1: float | None

    q3: float | None

    iqr: float | None


class NormalityResult(BaseModel):

    test: str

    statistic: float | None

    p_value: float | None

    alpha: float

    sample_size: int

    is_normal: bool | None

    interpretation: str


class HypothesisTestResult(BaseModel):

    test: str

    statistic: float | None

    p_value: float | None

    alpha: float

    significant: bool | None

    alternative: str

    interpretation: str


class StatisticalPhaseResult(BaseModel):

    descriptive: DescriptiveStatistics

    normality: NormalityResult


class InventoryStatisticalComparison(BaseModel):

    indicator: str

    indicator_label: str

    paired_observations: int

    pre: StatisticalPhaseResult

    post: StatisticalPhaseResult

    selected_test: HypothesisTestResult

    difference_mean: float | None

    improvement_percent: float | None

    direction: str

    conclusion: str


class InventoryStatisticalAnalysisResponse(
    BaseModel
):

    business_series_id: int | None

    alpha: float

    pairing_method: str

    pre_observations: int

    post_observations: int

    paired_observations: int

    indicators: list[
        InventoryStatisticalComparison
    ]


class StatisticalAnalysisRequest(BaseModel):

    business_series_id: int | None = Field(
        default=None,
        gt=0
    )

    alpha: float = Field(
        default=0.05,
        gt=0,
        lt=1
    )

    indicators: list[str] = Field(
        default_factory=lambda: [
            "stockout_units",
            "overstock_units",
            "service_level",
        ]
    )

    @field_validator(
        "indicators"
    )
    @classmethod
    def validate_indicators(
        cls,
        values: list[str]
    ) -> list[str]:

        supported = {
            "stockout_units",
            "overstock_units",
            "service_level",
            "closing_stock",
            "forecast_absolute_error",
            "forecast_ape",
        }

        normalized = []

        for value in values:

            value = (
                value
                .strip()
                .lower()
            )

            if value not in supported:

                raise ValueError(
                    "Indicador no soportado: "
                    f"{value}. "
                    "Permitidos: "
                    f"{sorted(supported)}"
                )

            if value not in normalized:

                normalized.append(
                    value
                )

        if not normalized:

            raise ValueError(
                "Debe seleccionar al menos "
                "un indicador"
            )

        return normalized