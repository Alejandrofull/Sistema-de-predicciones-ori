from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Training(Base):
    __tablename__ = "trainings"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    dataset_id: Mapped[int] = mapped_column(
        ForeignKey("datasets.id"),
        nullable=False
    )

    model_id: Mapped[int | None] = mapped_column(
        ForeignKey("models.id"),
        nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="pending"
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
        default=datetime.utcnow,
        nullable=False
    )