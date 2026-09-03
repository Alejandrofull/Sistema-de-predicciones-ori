from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class ExternalVariableValue(Base):
    __tablename__ = "external_variable_values"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    variable_id: Mapped[int] = mapped_column(
        ForeignKey(
            "external_variables.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    reference_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True
    )

    numeric_value: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    text_value: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    business_key: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
        index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )