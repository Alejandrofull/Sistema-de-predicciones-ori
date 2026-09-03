from datetime import datetime, timezone

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class UserRole(Base):
    __tablename__ = "user_roles"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "role_id",
            name="uq_user_role"
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    role_id: Mapped[int] = mapped_column(
        ForeignKey(
            "roles.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )