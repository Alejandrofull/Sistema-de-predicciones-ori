from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.retraining_policies import (
    RetrainingPolicy,
)


class RetrainingPolicyRepository:

    @staticmethod
    def create(
        db: Session,
        model_id: int,
        trigger_type: str,
        metric_name: str | None,
        threshold: float | None,
        is_active: bool = True
    ) -> RetrainingPolicy:

        policy = RetrainingPolicy(
            model_id=model_id,
            trigger_type=trigger_type,
            metric_name=metric_name,
            threshold=threshold,
            is_active=is_active
        )

        db.add(policy)
        db.commit()
        db.refresh(policy)

        return policy

    @staticmethod
    def get_by_id(
        db: Session,
        policy_id: int
    ) -> RetrainingPolicy | None:

        return db.get(
            RetrainingPolicy,
            policy_id
        )

    @staticmethod
    def get_all(
        db: Session,
        include_inactive: bool = False
    ) -> list[RetrainingPolicy]:

        statement = (
            select(RetrainingPolicy)
            .order_by(
                RetrainingPolicy.created_at.desc()
            )
        )

        if not include_inactive:

            statement = statement.where(
                RetrainingPolicy.is_active.is_(
                    True
                )
            )

        return list(
            db.scalars(
                statement
            ).all()
        )

    @staticmethod
    def get_by_model(
        db: Session,
        model_id: int,
        active_only: bool = False
    ) -> list[RetrainingPolicy]:

        statement = (
            select(RetrainingPolicy)
            .where(
                RetrainingPolicy.model_id
                == model_id
            )
            .order_by(
                RetrainingPolicy.created_at.asc()
            )
        )

        if active_only:

            statement = statement.where(
                RetrainingPolicy.is_active.is_(
                    True
                )
            )

        return list(
            db.scalars(
                statement
            ).all()
        )

    @staticmethod
    def update(
        db: Session,
        policy: RetrainingPolicy,
        trigger_type: str,
        metric_name: str | None,
        threshold: float | None,
        is_active: bool
    ) -> RetrainingPolicy:

        policy.trigger_type = trigger_type
        policy.metric_name = metric_name
        policy.threshold = threshold
        policy.is_active = is_active

        db.commit()
        db.refresh(policy)

        return policy

    @staticmethod
    def set_active(
        db: Session,
        policy: RetrainingPolicy,
        is_active: bool
    ) -> RetrainingPolicy:

        policy.is_active = is_active

        db.commit()
        db.refresh(policy)

        return policy

    @staticmethod
    def delete(
        db: Session,
        policy: RetrainingPolicy
    ) -> None:

        db.delete(policy)
        db.commit()