# app/schemas/statistics.py
from __future__ import annotations

import math
from typing import Annotated

from pydantic import (
    BaseModel,
    BeforeValidator,
    Field,
    field_validator,
)


def _sanitize_nan(value):
    """Convierte NaN/±Infinito en None (numpy/scipy los producen cuando
    una estadística no es calculable, p. ej. desv. estándar de n=1 o
    división por cero al calcular el % de mejora)."""
    if value is None:
        return None
    try:
        numero = float(value)
    except (TypeError, ValueError):
        return value
    if math.isnan(numero) or math.isinf(numero):
        return None
    return numero


SafeFloat = Annotated[float | None, BeforeValidator(_sanitize_nan)]


class DescriptiveStatistics(BaseModel):
    count: int
    mean: SafeFloat
    median: SafeFloat
    standard_deviation: SafeFloat
    variance: SafeFloat
    minimum: SafeFloat
    maximum: SafeFloat
    q1: SafeFloat
    q3: SafeFloat
    iqr: SafeFloat


class NormalityResult(BaseModel):
    test: str
    statistic: SafeFloat
    p_value: SafeFloat
    alpha: float
    sample_size: int
    is_normal: bool | None
    interpretation: str


class HypothesisTestResult(BaseModel):
    test: str
    statistic: SafeFloat
    p_value: SafeFloat
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
    difference_mean: SafeFloat
    improvement_percent: SafeFloat
    direction: str
    conclusion: str


class InventoryStatisticalAnalysisResponse(BaseModel):
    business_series_id: int | None
    alpha: float
    pairing_method: str
    pre_observations: int
    post_observations: int
    paired_observations: int
    indicators: list[InventoryStatisticalComparison]


class StatisticalAnalysisRequest(BaseModel):
    business_series_id: int | None = Field(default=None, gt=0)
    alpha: float = Field(default=0.05, gt=0, lt=1)
    indicators: list[str] = Field(
        default_factory=lambda: ["stockout_units", "overstock_units", "service_level"]
    )

    @field_validator("indicators")
    @classmethod
    def validate_indicators(cls, values: list[str]) -> list[str]:
        supported = {
            "stockout_units", "overstock_units", "service_level",
            "closing_stock", "forecast_absolute_error", "forecast_ape",
        }
        normalized = []
        for value in values:
            value = value.strip().lower()
            if value not in supported:
                raise ValueError(f"Indicador no soportado: {value}. Permitidos: {sorted(supported)}")
            if value not in normalized:
                normalized.append(value)
        if not normalized:
            raise ValueError("Debe seleccionar al menos un indicador")
        return normalized