from datetime import (
    datetime,
    timezone,
)

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from app.database.base import Base


class MLModel(Base):
    __tablename__ = "models"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    business_series_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "business_series.id",
            ondelete="SET NULL"
        ),
        nullable=True,
        index=True
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    model_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )

    version: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    metric_value: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(
            timezone.utc
        ),
        nullable=False
    )