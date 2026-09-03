from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class RetrainingRun(Base):
    __tablename__ = "retraining_runs"

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

    previous_version_id: Mapped[int | None] = mapped_column(
        ForeignKey("model_versions.id"),
        nullable=True
    )

    new_version_id: Mapped[int | None] = mapped_column(
        ForeignKey("model_versions.id"),
        nullable=True
    )

    dataset_id: Mapped[int] = mapped_column(
        ForeignKey("datasets.id"),
        nullable=False
    )

    trigger_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="pending",
        nullable=False
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )