from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories.model_repository import (
    ModelRepository,
)

from app.repositories.retraining_policy_repository import (
    RetrainingPolicyRepository,
)


class RetrainingPolicyService:

    @staticmethod
    def create(
        db: Session,
        model_id: int,
        trigger_type: str,
        metric_name: str | None,
        threshold: float | None,
        is_active: bool
    ):

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

        return (
            RetrainingPolicyRepository.create(
                db=db,
                model_id=model_id,
                trigger_type=trigger_type,
                metric_name=metric_name,
                threshold=threshold,
                is_active=is_active
            )
        )

    @staticmethod
    def update(
        db: Session,
        policy_id: int,
        trigger_type: str,
        metric_name: str | None,
        threshold: float | None,
        is_active: bool
    ):

        policy = (
            RetrainingPolicyRepository.get_by_id(
                db,
                policy_id
            )
        )

        if not policy:

            raise HTTPException(
                status_code=404,
                detail=(
                    "Política de reentrenamiento "
                    "no encontrada"
                )
            )

        return (
            RetrainingPolicyRepository.update(
                db=db,
                policy=policy,
                trigger_type=trigger_type,
                metric_name=metric_name,
                threshold=threshold,
                is_active=is_active
            )
        )

    @staticmethod
    def set_status(
        db: Session,
        policy_id: int,
        is_active: bool
    ):

        policy = (
            RetrainingPolicyRepository.get_by_id(
                db,
                policy_id
            )
        )

        if not policy:

            raise HTTPException(
                status_code=404,
                detail=(
                    "Política de reentrenamiento "
                    "no encontrada"
                )
            )

        return (
            RetrainingPolicyRepository.set_active(
                db=db,
                policy=policy,
                is_active=is_active
            )
        )

    @staticmethod
    def delete(
        db: Session,
        policy_id: int
    ) -> None:

        policy = (
            RetrainingPolicyRepository.get_by_id(
                db,
                policy_id
            )
        )

        if not policy:

            raise HTTPException(
                status_code=404,
                detail=(
                    "Política de reentrenamiento "
                    "no encontrada"
                )
            )

        RetrainingPolicyRepository.delete(
            db=db,
            policy=policy
        )