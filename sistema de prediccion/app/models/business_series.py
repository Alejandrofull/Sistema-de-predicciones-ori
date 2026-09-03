from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class BusinessSeries(Base):
    __tablename__ = "business_series"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    external_entity_id: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        index=True
    )

    entity_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    dimensions: Mapped[dict | None] = mapped_column(
        JSON,
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