from datetime import datetime, timezone

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Export(Base):
    __tablename__ = "exports"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    export_format: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True
    )

    storage_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        unique=True
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="completed",
        nullable=False,
        index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )