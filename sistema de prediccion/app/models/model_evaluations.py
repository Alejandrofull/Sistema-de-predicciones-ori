from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class ModelEvaluation(Base):
    __tablename__ = "model_evaluations"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    model_id: Mapped[int] = mapped_column(
        ForeignKey(
            "models.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    model_version_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "model_versions.id",
            ondelete="SET NULL"
        ),
        nullable=True,
        index=True
    )

    training_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "trainings.id",
            ondelete="SET NULL"
        ),
        nullable=True,
        index=True
    )

    dataset_id: Mapped[int] = mapped_column(
        ForeignKey(
            "datasets.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    evaluation_type: Mapped[str] = mapped_column(
        String(50),
        default="backtest",
        nullable=False,
        index=True
    )

    mae: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    mse: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    rmse: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    mape: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    smape: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    r2: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    training_time_seconds: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    prediction_time_seconds: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    ranking_position: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )

    is_best_model: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True
    )

    evaluation_config: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )