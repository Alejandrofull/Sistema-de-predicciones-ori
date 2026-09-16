# Importar aquí cada fuente para que se registre automáticamente al arrancar la app.
# Cuando agregues una nueva fuente, créala en su propio archivo (siguiendo el
# patrón de business_series_source.py) y agrega su import aquí.
from . import business_series_source  # noqa: F401
from . import predictions_source  # noqa: F401
from . import inventory_observations_source  # noqa: F401

from .registry import (  # noqa: F401
    get_source,
    list_sources,
    list_sources_for_user,
    user_can_access_source,
)
