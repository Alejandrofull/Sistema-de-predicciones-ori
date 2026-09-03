from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class RetrainingPolicy(Base):
    __tablename__ = "retraining_policies"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    model_id: Mapped[int] = mapped_column(
        ForeignKey("models.id"),
        nullable=False,
        index=True
    )

    trigger_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    metric_name: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    threshold: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )