from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class ModelDeployment(Base):
    __tablename__ = "model_deployments"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    model_version_id: Mapped[int] = mapped_column(
        ForeignKey("model_versions.id"),
        nullable=False,
        index=True
    )

    environment: Mapped[str] = mapped_column(
        String(30),
        default="production",
        nullable=False
    )

    deployment_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False
    )

    is_current: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    deployed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    deactivated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )