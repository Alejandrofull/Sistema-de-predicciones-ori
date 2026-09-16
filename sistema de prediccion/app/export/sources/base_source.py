from abc import ABC, abstractmethod
from datetime import date
from typing import Any

import pandas as pd
from sqlalchemy.orm import Session


class ExportSource(ABC):
    """
    Representa UNA fuente de datos real del sistema que puede exportarse
    (ej: series de negocio, predicciones, inventario). Cada fuente sabe:
      - qué filtros acepta (para que el frontend los renderice dinámicamente,
        incluyendo opciones dinámicas como la lista de series de negocio)
      - cómo consultar los datos reales, ya filtrados y con el permiso
        del usuario validado del lado del servidor.

    El frontend NUNCA envía los registros a exportar, solo el `key` de la
    fuente y los valores de los filtros. Los datos siempre se obtienen
    aquí, en el backend, usando los repositorios reales de la app.
    """

    key: str
    label: str

    # Código de permiso (de app.security.permissions.Permissions) requerido
    # para usar esta fuente específica. None = solo se requiere el permiso
    # general de exportar (EXPORTS_GENERATE), validado a nivel de router.
    required_permission: str | None = None

    @abstractmethod
    def get_filters_schema(self, db: Session, current_user: Any) -> list[dict[str, Any]]:
        """
        Describe los filtros que el frontend debe renderizar.
        Recibe db/current_user porque algunos filtros necesitan opciones
        dinámicas (ej: lista de series de negocio activas) en vez de
        estar fijas de antemano.

        Cada filtro: {"name": str, "label": str, "type": "text"|"date"|"boolean"|"select",
                       "options"?: [{"value": ..., "label": ...}], "default"?: Any}
        """
        raise NotImplementedError

    @abstractmethod
    def fetch(self, db: Session, current_user: Any, filters: dict[str, Any]) -> pd.DataFrame:
        """
        Ejecuta la consulta real (usando los repositorios de la app o una
        query propia) y devuelve un DataFrame listo para exportar.
        """
        raise NotImplementedError


def parse_date_filter(value: Any) -> date | None:
    """Convierte un filtro de fecha (string ISO 'YYYY-MM-DD' u objeto date) a date, o None si viene vacío."""
    if not value:
        return None
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))
