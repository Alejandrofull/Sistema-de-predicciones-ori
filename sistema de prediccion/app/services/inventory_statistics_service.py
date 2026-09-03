from __future__ import annotations

import math

import numpy as np

from fastapi import HTTPException
from scipy import stats
from sqlalchemy.orm import Session

from app.repositories.business_series_repository import (
    BusinessSeriesRepository,
)

from app.repositories.inventory_observation_repository import (
    InventoryObservationRepository,
)


class InventoryStatisticsService:

    INDICATOR_LABELS = {
        "stockout_units": (
            "Unidades en quiebre de stock"
        ),
        "overstock_units": (
            "Unidades de sobrestock"
        ),
        "service_level": (
            "Nivel de servicio"
        ),
        "closing_stock": (
            "Inventario final"
        ),
        "forecast_absolute_error": (
            "Error absoluto del pronóstico"
        ),
        "forecast_ape": (
            "Error porcentual absoluto"
        ),
    }

    LOWER_IS_BETTER = {
        "stockout_units",
        "overstock_units",
        "closing_stock",
        "forecast_absolute_error",
        "forecast_ape",
    }

    HIGHER_IS_BETTER = {
        "service_level",
    }

    # ==========================================
    # ANÁLISIS GENERAL
    # ==========================================

    def analyze(
        self,
        db: Session,
        business_series_id: int | None,
        indicators: list[str],
        alpha: float = 0.05
    ) -> dict:

        if business_series_id is not None:

            business_series = (
                BusinessSeriesRepository
                .get_by_id(
                    db,
                    business_series_id
                )
            )

            if not business_series:

                raise HTTPException(
                    status_code=404,
                    detail=(
                        "Serie de negocio "
                        "no encontrada"
                    )
                )

        pre_observations = (
            InventoryObservationRepository
            .get_all(
                db=db,
                phase="pre",
                business_series_id=(
                    business_series_id
                ),
                limit=100000
            )
        )

        post_observations = (
            InventoryObservationRepository
            .get_all(
                db=db,
                phase="post",
                business_series_id=(
                    business_series_id
                ),
                limit=100000
            )
        )

        if not pre_observations:

            raise HTTPException(
                status_code=400,
                detail=(
                    "No existen observaciones "
                    "PRE para realizar "
                    "el análisis"
                )
            )

        if not post_observations:

            raise HTTPException(
                status_code=400,
                detail=(
                    "No existen observaciones "
                    "POST para realizar "
                    "el análisis"
                )
            )

        # ==========================================
        # EMPAREJAMIENTO
        # ==========================================

        pairs = (
            self._pair_observations(
                pre_observations=(
                    pre_observations
                ),
                post_observations=(
                    post_observations
                )
            )
        )

        if len(pairs) < 3:

            raise HTTPException(
                status_code=400,
                detail=(
                    "Se requieren al menos "
                    "3 pares PRE/POST para "
                    "realizar las pruebas "
                    "estadísticas"
                )
            )

        results = []

        for indicator in indicators:

            comparison = (
                self._analyze_indicator(
                    indicator=indicator,
                    pairs=pairs,
                    alpha=alpha
                )
            )

            results.append(
                comparison
            )

        return {
            "business_series_id": (
                business_series_id
            ),
            "alpha": (
                float(
                    alpha
                )
            ),
            "pairing_method": (
                "Emparejamiento cronológico "
                "por posición dentro de "
                "cada serie de negocio"
            ),
            "pre_observations": (
                len(
                    pre_observations
                )
            ),
            "post_observations": (
                len(
                    post_observations
                )
            ),
            "paired_observations": (
                len(
                    pairs
                )
            ),
            "indicators": (
                results
            )
        }

    # ==========================================
    # EMPAREJAR OBSERVACIONES
    # ==========================================

    def _pair_observations(
        self,
        pre_observations: list,
        post_observations: list
    ) -> list[tuple]:

        # ==========================================
        # AGRUPAR POR SERIE
        # ==========================================

        pre_by_series = {}

        post_by_series = {}

        for observation in pre_observations:

            pre_by_series.setdefault(
                observation.business_series_id,
                []
            ).append(
                observation
            )

        for observation in post_observations:

            post_by_series.setdefault(
                observation.business_series_id,
                []
            ).append(
                observation
            )

        pairs = []

        series_ids = (
            set(
                pre_by_series.keys()
            )
            &
            set(
                post_by_series.keys()
            )
        )

        for series_id in sorted(
            series_ids
        ):

            pre_items = sorted(
                pre_by_series[
                    series_id
                ],
                key=lambda item: (
                    item.observation_date,
                    item.id
                )
            )

            post_items = sorted(
                post_by_series[
                    series_id
                ],
                key=lambda item: (
                    item.observation_date,
                    item.id
                )
            )

            pair_count = min(
                len(
                    pre_items
                ),
                len(
                    post_items
                )
            )

            for index in range(
                pair_count
            ):

                pairs.append(
                    (
                        pre_items[
                            index
                        ],
                        post_items[
                            index
                        ],
                    )
                )

        return pairs

    # ==========================================
    # ANALIZAR INDICADOR
    # ==========================================

    def _analyze_indicator(
        self,
        indicator: str,
        pairs: list[tuple],
        alpha: float
    ) -> dict:

        pre_values = []

        post_values = []

        for (
            pre_observation,
            post_observation
        ) in pairs:

            pre_value = (
                self._indicator_value(
                    observation=(
                        pre_observation
                    ),
                    indicator=indicator
                )
            )

            post_value = (
                self._indicator_value(
                    observation=(
                        post_observation
                    ),
                    indicator=indicator
                )
            )

            # Para errores de pronóstico
            # puede no existir predicted_demand.
            if (
                pre_value is None
                or post_value is None
            ):
                continue

            if not (
                math.isfinite(
                    pre_value
                )
                and math.isfinite(
                    post_value
                )
            ):
                continue

            pre_values.append(
                float(
                    pre_value
                )
            )

            post_values.append(
                float(
                    post_value
                )
            )

        if len(pre_values) < 3:

            raise HTTPException(
                status_code=400,
                detail=(
                    f"El indicador '{indicator}' "
                    "no tiene al menos 3 pares "
                    "válidos PRE/POST"
                )
            )

        pre_array = np.asarray(
            pre_values,
            dtype=float
        )

        post_array = np.asarray(
            post_values,
            dtype=float
        )

        differences = (
            post_array
            -
            pre_array
        )

        pre_descriptive = (
            self._descriptive_statistics(
                pre_array
            )
        )

        post_descriptive = (
            self._descriptive_statistics(
                post_array
            )
        )

        # ==========================================
        # NORMALIDAD
        #
        # En una prueba pareada interesa
        # especialmente la normalidad de las
        # diferencias.
        # ==========================================

        pre_normality = (
            self._shapiro(
                pre_array,
                alpha
            )
        )

        post_normality = (
            self._shapiro(
                post_array,
                alpha
            )
        )

        difference_normality = (
            self._shapiro(
                differences,
                alpha
            )
        )

        # ==========================================
        # SELECCIÓN DE PRUEBA
        # ==========================================

        if (
            difference_normality[
                "is_normal"
            ]
            is True
        ):

            test_result = (
                self._paired_t_test(
                    pre_values=(
                        pre_array
                    ),
                    post_values=(
                        post_array
                    ),
                    alpha=alpha
                )
            )

        else:

            test_result = (
                self._wilcoxon_test(
                    pre_values=(
                        pre_array
                    ),
                    post_values=(
                        post_array
                    ),
                    alpha=alpha
                )
            )

        difference_mean = float(
            np.mean(
                post_array
                -
                pre_array
            )
        )

        improvement_percent = (
            self._calculate_improvement(
                indicator=indicator,
                pre_mean=(
                    pre_descriptive[
                        "mean"
                    ]
                ),
                post_mean=(
                    post_descriptive[
                        "mean"
                    ]
                )
            )
        )

        direction = (
            self._direction(
                indicator=indicator,
                pre_mean=(
                    pre_descriptive[
                        "mean"
                    ]
                ),
                post_mean=(
                    post_descriptive[
                        "mean"
                    ]
                )
            )
        )

        conclusion = (
            self._build_conclusion(
                indicator=indicator,
                test_result=(
                    test_result
                ),
                direction=direction,
                pre_mean=(
                    pre_descriptive[
                        "mean"
                    ]
                ),
                post_mean=(
                    post_descriptive[
                        "mean"
                    ]
                ),
                improvement_percent=(
                    improvement_percent
                )
            )
        )

        # Conservamos la normalidad PRE y POST
        # en sus bloques correspondientes.
        #
        # La prueba seleccionada se decide con
        # la normalidad de las diferencias.

        pre_normality[
            "interpretation"
        ] += (
            " La selección de la prueba "
            "inferencial se realizó usando "
            "la normalidad de las diferencias "
            "PRE-POST."
        )

        post_normality[
            "interpretation"
        ] += (
            " La selección de la prueba "
            "inferencial se realizó usando "
            "la normalidad de las diferencias "
            "PRE-POST."
        )

        test_result[
            "interpretation"
        ] += (
            " Normalidad de las diferencias: "
            f"{difference_normality['interpretation']}"
        )

        return {
            "indicator": indicator,
            "indicator_label": (
                self.INDICATOR_LABELS[
                    indicator
                ]
            ),
            "paired_observations": (
                len(
                    pre_array
                )
            ),
            "pre": {
                "descriptive": (
                    pre_descriptive
                ),
                "normality": (
                    pre_normality
                )
            },
            "post": {
                "descriptive": (
                    post_descriptive
                ),
                "normality": (
                    post_normality
                )
            },
            "selected_test": (
                test_result
            ),
            "difference_mean": (
                difference_mean
            ),
            "improvement_percent": (
                improvement_percent
            ),
            "direction": (
                direction
            ),
            "conclusion": (
                conclusion
            )
        }

    # ==========================================
    # OBTENER INDICADOR POR OBSERVACIÓN
    # ==========================================

    @staticmethod
    def _indicator_value(
        observation,
        indicator: str
    ) -> float | None:

        opening_stock = float(
            observation.opening_stock
        )

        replenishment = float(
            observation.replenishment_quantity
        )

        demand = float(
            observation.actual_demand
        )

        available = (
            opening_stock
            +
            replenishment
        )

        if indicator == "stockout_units":

            return max(
                demand - available,
                0.0
            )

        if indicator == "overstock_units":

            return max(
                available - demand,
                0.0
            )

        if indicator == "service_level":

            if demand <= 0:
                return 100.0

            served = min(
                available,
                demand
            )

            return (
                served
                /
                demand
                *
                100.0
            )

        if indicator == "closing_stock":

            return float(
                observation.closing_stock
            )

        if (
            indicator
            == "forecast_absolute_error"
        ):

            if (
                observation.predicted_demand
                is None
            ):
                return None

            return abs(
                demand
                -
                float(
                    observation.predicted_demand
                )
            )

        if indicator == "forecast_ape":

            if (
                observation.predicted_demand
                is None
            ):
                return None

            if demand == 0:
                return None

            return (
                abs(
                    demand
                    -
                    float(
                        observation.predicted_demand
                    )
                )
                /
                abs(
                    demand
                )
                *
                100.0
            )

        raise ValueError(
            "Indicador no soportado: "
            f"{indicator}"
        )

    # ==========================================
    # ESTADÍSTICA DESCRIPTIVA
    # ==========================================

    @staticmethod
    def _descriptive_statistics(
        values: np.ndarray
    ) -> dict:

        if len(values) == 0:

            return {
                "count": 0,
                "mean": None,
                "median": None,
                "standard_deviation": None,
                "variance": None,
                "minimum": None,
                "maximum": None,
                "q1": None,
                "q3": None,
                "iqr": None,
            }

        q1 = float(
            np.percentile(
                values,
                25
            )
        )

        q3 = float(
            np.percentile(
                values,
                75
            )
        )

        if len(values) > 1:

            standard_deviation = float(
                np.std(
                    values,
                    ddof=1
                )
            )

            variance = float(
                np.var(
                    values,
                    ddof=1
                )
            )

        else:

            standard_deviation = None
            variance = None

        return {
            "count": int(
                len(
                    values
                )
            ),
            "mean": float(
                np.mean(
                    values
                )
            ),
            "median": float(
                np.median(
                    values
                )
            ),
            "standard_deviation": (
                standard_deviation
            ),
            "variance": (
                variance
            ),
            "minimum": float(
                np.min(
                    values
                )
            ),
            "maximum": float(
                np.max(
                    values
                )
            ),
            "q1": q1,
            "q3": q3,
            "iqr": float(
                q3 - q1
            ),
        }

    # ==========================================
    # SHAPIRO-WILK
    # ==========================================

    @staticmethod
    def _shapiro(
        values: np.ndarray,
        alpha: float
    ) -> dict:

        sample_size = len(
            values
        )

        if sample_size < 3:

            return {
                "test": "Shapiro-Wilk",
                "statistic": None,
                "p_value": None,
                "alpha": float(
                    alpha
                ),
                "sample_size": (
                    sample_size
                ),
                "is_normal": None,
                "interpretation": (
                    "No existen suficientes "
                    "observaciones para aplicar "
                    "Shapiro-Wilk."
                )
            }

        # scipy recomienda precaución con el
        # p-value de Shapiro para n > 5000.
        sample = values

        if sample_size > 5000:

            sample = values[
                :5000
            ]

        # Si todos los valores son exactamente
        # iguales, no tiene sentido interpretar
        # Shapiro de la forma habitual.
        if np.allclose(
            sample,
            sample[0]
        ):

            return {
                "test": "Shapiro-Wilk",
                "statistic": 1.0,
                "p_value": 1.0,
                "alpha": float(
                    alpha
                ),
                "sample_size": int(
                    sample_size
                ),
                "is_normal": True,
                "interpretation": (
                    "Los valores son constantes; "
                    "no se observa variabilidad "
                    "para evaluar una desviación "
                    "de normalidad."
                )
            }

        statistic, p_value = (
            stats.shapiro(
                sample
            )
        )

        is_normal = (
            float(
                p_value
            )
            >
            alpha
        )

        if is_normal:

            interpretation = (
                "No se rechaza la hipótesis "
                "de normalidad "
                f"(p={float(p_value):.6f} "
                f"> α={alpha})."
            )

        else:

            interpretation = (
                "Se rechaza la hipótesis "
                "de normalidad "
                f"(p={float(p_value):.6f} "
                f"≤ α={alpha})."
            )

        return {
            "test": "Shapiro-Wilk",
            "statistic": float(
                statistic
            ),
            "p_value": float(
                p_value
            ),
            "alpha": float(
                alpha
            ),
            "sample_size": int(
                sample_size
            ),
            "is_normal": bool(
                is_normal
            ),
            "interpretation": (
                interpretation
            )
        }

    # ==========================================
    # T DE STUDENT PAREADA
    # ==========================================

    @staticmethod
    def _paired_t_test(
        pre_values: np.ndarray,
        post_values: np.ndarray,
        alpha: float
    ) -> dict:

        statistic, p_value = (
            stats.ttest_rel(
                pre_values,
                post_values,
                nan_policy="omit"
            )
        )

        statistic = float(
            statistic
        )

        p_value = float(
            p_value
        )

        significant = (
            p_value
            <
            alpha
        )

        if significant:

            interpretation = (
                "Existe una diferencia "
                "estadísticamente significativa "
                "entre las mediciones PRE "
                "y POST mediante t de Student "
                "para muestras relacionadas."
            )

        else:

            interpretation = (
                "No se encontró una diferencia "
                "estadísticamente significativa "
                "entre las mediciones PRE "
                "y POST mediante t de Student "
                "para muestras relacionadas."
            )

        return {
            "test": (
                "t de Student para "
                "muestras relacionadas"
            ),
            "statistic": statistic,
            "p_value": p_value,
            "alpha": float(
                alpha
            ),
            "significant": (
                significant
            ),
            "alternative": (
                "two-sided"
            ),
            "interpretation": (
                interpretation
            )
        }

    # ==========================================
    # WILCOXON
    # ==========================================

    @staticmethod
    def _wilcoxon_test(
        pre_values: np.ndarray,
        post_values: np.ndarray,
        alpha: float
    ) -> dict:

        differences = (
            post_values
            -
            pre_values
        )

        # Si absolutamente todos los pares
        # son iguales, scipy.wilcoxon puede
        # resultar problemático.
        if np.allclose(
            differences,
            0.0
        ):

            return {
                "test": (
                    "Wilcoxon para muestras "
                    "relacionadas"
                ),
                "statistic": 0.0,
                "p_value": 1.0,
                "alpha": float(
                    alpha
                ),
                "significant": False,
                "alternative": (
                    "two-sided"
                ),
                "interpretation": (
                    "Todas las diferencias "
                    "PRE-POST son iguales a "
                    "cero; no existe evidencia "
                    "de diferencia entre fases."
                )
            }

        statistic, p_value = (
            stats.wilcoxon(
                pre_values,
                post_values,
                alternative="two-sided",
                zero_method="wilcox"
            )
        )

        statistic = float(
            statistic
        )

        p_value = float(
            p_value
        )

        significant = (
            p_value
            <
            alpha
        )

        if significant:

            interpretation = (
                "Existe una diferencia "
                "estadísticamente significativa "
                "entre las mediciones PRE "
                "y POST mediante la prueba "
                "de rangos con signo "
                "de Wilcoxon."
            )

        else:

            interpretation = (
                "No se encontró una diferencia "
                "estadísticamente significativa "
                "entre las mediciones PRE "
                "y POST mediante la prueba "
                "de rangos con signo "
                "de Wilcoxon."
            )

        return {
            "test": (
                "Wilcoxon para muestras "
                "relacionadas"
            ),
            "statistic": statistic,
            "p_value": p_value,
            "alpha": float(
                alpha
            ),
            "significant": (
                significant
            ),
            "alternative": (
                "two-sided"
            ),
            "interpretation": (
                interpretation
            )
        }

    # ==========================================
    # MEJORA PORCENTUAL
    # ==========================================

    def _calculate_improvement(
        self,
        indicator: str,
        pre_mean: float | None,
        post_mean: float | None
    ) -> float | None:

        if (
            pre_mean is None
            or post_mean is None
        ):

            return None

        if pre_mean == 0:

            if post_mean == 0:

                return 0.0

            return None

        if indicator in self.LOWER_IS_BETTER:

            return float(
                (
                    pre_mean
                    -
                    post_mean
                )
                /
                abs(
                    pre_mean
                )
                *
                100.0
            )

        if indicator in self.HIGHER_IS_BETTER:

            return float(
                (
                    post_mean
                    -
                    pre_mean
                )
                /
                abs(
                    pre_mean
                )
                *
                100.0
            )

        return None

    # ==========================================
    # DIRECCIÓN DEL CAMBIO
    # ==========================================

    def _direction(
        self,
        indicator: str,
        pre_mean: float | None,
        post_mean: float | None
    ) -> str:

        if (
            pre_mean is None
            or post_mean is None
        ):

            return "indeterminate"

        if np.isclose(
            pre_mean,
            post_mean
        ):

            return "stable"

        if indicator in self.LOWER_IS_BETTER:

            if post_mean < pre_mean:

                return "improved"

            return "worsened"

        if indicator in self.HIGHER_IS_BETTER:

            if post_mean > pre_mean:

                return "improved"

            return "worsened"

        return "indeterminate"

    # ==========================================
    # CONCLUSIÓN
    # ==========================================

    def _build_conclusion(
        self,
        indicator: str,
        test_result: dict,
        direction: str,
        pre_mean: float | None,
        post_mean: float | None,
        improvement_percent: float | None
    ) -> str:

        label = (
            self.INDICATOR_LABELS[
                indicator
            ]
        )

        if (
            pre_mean is None
            or post_mean is None
        ):

            return (
                f"No fue posible evaluar "
                f"el indicador '{label}'."
            )

        change_text = (
            f"La media PRE fue "
            f"{pre_mean:.4f} y la media "
            f"POST fue {post_mean:.4f}."
        )

        if improvement_percent is not None:

            improvement_text = (
                " La variación favorable "
                "calculada fue de "
                f"{improvement_percent:.2f}%."
            )

        else:

            improvement_text = ""

        significant = (
            test_result.get(
                "significant"
            )
        )

        p_value = (
            test_result.get(
                "p_value"
            )
        )

        if (
            significant is True
            and direction == "improved"
        ):

            return (
                f"{change_text}"
                f"{improvement_text} "
                f"La diferencia fue "
                f"estadísticamente "
                f"significativa "
                f"(p={p_value:.6f}), "
                f"mostrando una mejora "
                f"del indicador '{label}' "
                f"en la fase POST."
            )

        if (
            significant is True
            and direction == "worsened"
        ):

            return (
                f"{change_text} "
                f"La diferencia fue "
                f"estadísticamente "
                f"significativa "
                f"(p={p_value:.6f}), "
                f"pero el comportamiento "
                f"del indicador '{label}' "
                f"empeoró en la fase POST."
            )

        if significant is False:

            return (
                f"{change_text}"
                f"{improvement_text} "
                f"Sin embargo, la diferencia "
                f"no alcanzó significancia "
                f"estadística "
                f"(p={p_value:.6f})."
            )

        return (
            f"{change_text}"
            f"{improvement_text}"
        )