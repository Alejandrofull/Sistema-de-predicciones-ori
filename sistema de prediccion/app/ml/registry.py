from app.ml.models.arima.model import (
    ArimaDemandModel
)

from app.ml.models.hybrid.model import (
    HybridDemandModel
)

from app.ml.models.random_forest.model import (
    RandomForestDemandModel
)

from app.ml.models.xgboost.model import (
    XGBoostDemandModel
)


MODEL_REGISTRY = {
    "arima": ArimaDemandModel,
    "random_forest": (
        RandomForestDemandModel
    ),
    "xgboost": XGBoostDemandModel,
    "hybrid": HybridDemandModel
}


def get_model_class(
    model_name: str
):
    normalized = (
        model_name
        .lower()
        .strip()
    )

    model_class = (
        MODEL_REGISTRY.get(
            normalized
        )
    )

    if not model_class:
        raise ValueError(
            f"Modelo no soportado: "
            f"{model_name}"
        )

    return model_class


def get_supported_models() -> list[str]:

    return list(
        MODEL_REGISTRY.keys()
    )