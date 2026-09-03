from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    # Usuario específico que recibe la notificación.
    # Puede ser NULL si inicialmente se genera por rol.
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        nullable=True,
        index=True
    )

    # Rol al que va dirigida.
    # Ejemplos: admin, operator
    recipient_role: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True
    )

    # Categoría general.
    # model, training, demand, inventory, stock, retraining, system
    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )

    # Evento concreto.
    # training_completed, stock_alert, demand_alert...
    notification_type: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
        index=True
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )

    message: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    # info, low, medium, high, critical
    priority: Mapped[str] = mapped_column(
        String(30),
        default="info",
        nullable=False,
        index=True
    )

    # Indica si el usuario debería tomar una acción.
    requires_action: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    # Acción sugerida al operario.
    suggested_action: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    # Entidad relacionada:
    # product, model, training, prediction...
    entity_type: Mapped[str | None] = mapped_column(
        String(80),
        nullable=True,
        index=True
    )

    entity_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True
    )

    # Información adicional para la interfaz.
    # Ej:
    # {
    #   "stock_actual": 85,
    #   "demanda_proyectada": 140,
    #   "deficit": 55
    # }
    payload: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True
    )

    is_read: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True
    )

    read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Para alertas importantes:
    # confirma que el operario/admin tomó conocimiento.
    acknowledged: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    acknowledged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )