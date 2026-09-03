from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Permission(Base):
    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    name: Mapped[str] = mapped_column(
        String(120),
        nullable=False
    )

    code: Mapped[str] = mapped_column(
        String(120),
        unique=True,
        nullable=False,
        index=True
    )

    module: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
        index=True
    )

    description: Mapped[str | None] = mapped_column(
        String(255),
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