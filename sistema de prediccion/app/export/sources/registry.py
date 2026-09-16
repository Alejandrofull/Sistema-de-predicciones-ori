from sqlalchemy.orm import Session

from app.services.authorization_service import AuthorizationService

from .base_source import ExportSource

_REGISTRY: dict[str, ExportSource] = {}


def register_source(source: ExportSource) -> None:
    if source.key in _REGISTRY:
        raise ValueError(f"La fuente de exportación '{source.key}' ya está registrada")
    _REGISTRY[source.key] = source


def get_source(key: str) -> ExportSource:
    if key not in _REGISTRY:
        raise ValueError(f"Fuente de exportación desconocida: '{key}'")
    return _REGISTRY[key]


def list_sources() -> list[ExportSource]:
    return list(_REGISTRY.values())


def user_can_access_source(db: Session, current_user, source: ExportSource) -> bool:
    if source.required_permission is None:
        return True
    return AuthorizationService.has_permission(
        db=db,
        user_id=current_user.id,
        permission_code=source.required_permission,
    )


def list_sources_for_user(db: Session, current_user) -> list[ExportSource]:
    """Filtra las fuentes según el permiso específico de cada una (si tiene)."""
    return [source for source in _REGISTRY.values() if user_can_access_source(db, current_user, source)]
