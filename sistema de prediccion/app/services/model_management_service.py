from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories.model_repository import (
    ModelRepository,
)

from app.repositories.model_version_repository import (
    ModelVersionRepository,
)

from app.services.audit_service import (
    AuditService,
)


class ModelManagementService:

    @staticmethod
    def activate_model(
        db: Session,
        model_id: int,
        user_id: int
    ) -> dict:

        model = (
            ModelRepository.get_by_id(
                db,
                model_id
            )
        )

        if not model:

            raise HTTPException(
                status_code=404,
                detail="Modelo no encontrado"
            )

        latest_version = (
            ModelVersionRepository.get_latest(
                db,
                model.id
            )
        )

        if not latest_version:

            raise HTTPException(
                status_code=400,
                detail=(
                    "El modelo no tiene "
                    "versiones entrenadas"
                )
            )

        if not latest_version.artifact_path:

            raise HTTPException(
                status_code=400,
                detail=(
                    "La versión del modelo "
                    "no tiene artefacto almacenado"
                )
            )

        business_series_id = (
            model.business_series_id
        )

        previous_active_version = (
            ModelVersionRepository
            .get_active_by_model(
                db=db,
                model_id=model.id
            )
        )

        previous_active_version_id = (
            previous_active_version.id
            if previous_active_version
            else None
        )

        # ==========================================
        # DESACTIVAR MODELO ACTUAL DE LA SERIE
        # ==========================================

        ModelRepository.deactivate_by_business_series(
            db=db,
            business_series_id=(
                business_series_id
            )
        )

        # ==========================================
        # DESACTIVAR VERSIONES ACTIVAS DE LA SERIE
        # ==========================================

        ModelVersionRepository.deactivate_for_business_series(
            db=db,
            business_series_id=(
                business_series_id
            )
        )

        # ==========================================
        # ACTIVAR MODELO
        # ==========================================

        ModelRepository.set_active(
            db=db,
            model=model,
            active=True
        )

        # ==========================================
        # ACTIVAR ÚLTIMA VERSIÓN
        # ==========================================

        ModelVersionRepository.set_active(
            db=db,
            version=latest_version,
            active=True
        )

        # ==========================================
        # AUDITORÍA
        # ==========================================

        AuditService.log_safe(
            db=db,
            user_id=user_id,
            action="model.activate",
            entity="model",
            entity_id=model.id,
            details={
                "model_id": (
                    model.id
                ),
                "model_type": (
                    model.model_type
                ),
                "business_series_id": (
                    business_series_id
                ),
                "previous_active_version_id": (
                    previous_active_version_id
                ),
                "activated_version_id": (
                    latest_version.id
                ),
                "activated_version_number": (
                    latest_version.version_number
                )
            }
        )

        return {
            "model_id": (
                model.id
            ),
            "model_version_id": (
                latest_version.id
            ),
            "business_series_id": (
                business_series_id
            ),
            "model_type": (
                model.model_type
            ),
            "active": True,
            "message": (
                "Modelo activado "
                "correctamente"
            )
        }