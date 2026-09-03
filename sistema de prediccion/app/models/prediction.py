from datetime import (
    date,
    datetime,
    timezone,
)

from sqlalchemy import (
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from app.database.base import Base


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    user_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="SET NULL"
        ),
        nullable=True,
        index=True
    )

    model_id: Mapped[int] = mapped_column(
        ForeignKey(
            "models.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    model_version_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "model_versions.id",
            ondelete="SET NULL"
        ),
        nullable=True,
        index=True
    )

    dataset_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "datasets.id",
            ondelete="SET NULL"
        ),
        nullable=True,
        index=True
    )

    business_series_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "business_series.id",
            ondelete="SET NULL"
        ),
        nullable=True,
        index=True
    )

    horizon: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True
    )

    end_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="completed",
        nullable=False,
        index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(
            timezone.utc
        ),
        nullable=False,
        index=True
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )


class PredictionResult(Base):
    __tablename__ = "prediction_results"

    __table_args__ = (
        UniqueConstraint(
            "prediction_id",
            "prediction_date",
            name=(
                "uq_prediction_results_"
                "prediction_date"
            )
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    prediction_id: Mapped[int] = mapped_column(
        ForeignKey(
            "predictions.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    prediction_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True
    )

    predicted_value: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    actual_value: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    lower_bound: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    upper_bound: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(
            timezone.utc
        ),
        nullable=False
    )