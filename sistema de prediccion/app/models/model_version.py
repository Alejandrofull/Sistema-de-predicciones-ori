from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class ModelVersion(Base):
    __tablename__ = "model_versions"

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

    version_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    parameters: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True
    )

    feature_config: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True
    )

    artifact_path: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )