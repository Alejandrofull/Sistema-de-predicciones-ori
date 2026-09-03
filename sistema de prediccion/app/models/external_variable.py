from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class ExternalVariable(Base):
    __tablename__ = "external_variables"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True
    )

    variable_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    source_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    unit: Mapped[str | None] = mapped_column(
        String(50),
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