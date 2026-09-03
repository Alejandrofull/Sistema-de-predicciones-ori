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


class InventoryObservation(Base):
    __tablename__ = "inventory_observations"

    __table_args__ = (
        UniqueConstraint(
            "business_series_id",
            "observation_date",
            "phase",
            name=(
                "uq_inventory_observation_"
                "series_date_phase"
            )
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    business_series_id: Mapped[int] = mapped_column(
        ForeignKey(
            "business_series.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    user_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="SET NULL"
        ),
        nullable=True,
        index=True
    )

    observation_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True
    )

    # pre = antes de implementar ML
    # post = después de implementar ML
    phase: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True
    )

    # Stock disponible al inicio del periodo
    opening_stock: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    # Cantidad recibida/reposición
    replenishment_quantity: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False
    )

    # Demanda real del periodo
    actual_demand: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    # Inventario final real.
    # Puede ser enviado o calculado.
    closing_stock: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    # Demanda pronosticada, si existe.
    predicted_demand: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    source_type: Mapped[str] = mapped_column(
        String(50),
        default="manual",
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