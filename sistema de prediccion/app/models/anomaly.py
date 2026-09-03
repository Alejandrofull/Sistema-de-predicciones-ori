from datetime import (
    datetime,
    timezone,
)

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    UniqueConstraint,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from app.database.base import Base


class Anomaly(Base):
    __tablename__ = "anomalies"

    __table_args__ = (
        UniqueConstraint(
            "prediction_result_id",
            "anomaly_type",
            "method",
            name=(
                "uq_anomalies_"
                "prediction_result_type_method"
            )
        ),
    )

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

    model_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "models.id",
            ondelete="SET NULL"
        ),
        nullable=True,
        index=True
    )

    prediction_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "predictions.id",
            ondelete="CASCADE"
        ),
        nullable=True,
        index=True
    )

    prediction_result_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "prediction_results.id",
            ondelete="CASCADE"
        ),
        nullable=True,
        index=True
    )

    anomaly_type: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
        index=True
    )

    method: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )

    observed_value: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    expected_value: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    deviation: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    severity: Mapped[str] = mapped_column(
        String(30),
        default="medium",
        nullable=False,
        index=True
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="open",
        nullable=False,
        index=True
    )

    details: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True
    )

    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(
            timezone.utc
        ),
        nullable=False,
        index=True
    )

    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )