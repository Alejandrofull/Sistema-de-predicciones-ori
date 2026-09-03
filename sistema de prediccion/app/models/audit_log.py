from datetime import (
    datetime,
    timezone,
)

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from app.database.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

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

    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True
    )

    entity: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True
    )

    entity_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True
    )

    details: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(
            timezone.utc
        ),
        nullable=False,
        index=True
    )