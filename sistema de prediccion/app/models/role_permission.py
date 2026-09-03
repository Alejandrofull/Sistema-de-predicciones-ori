from datetime import datetime, timezone

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class RolePermission(Base):
    __tablename__ = "role_permissions"

    __table_args__ = (
        UniqueConstraint(
            "role_id",
            "permission_id",
            name="uq_role_permission"
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    role_id: Mapped[int] = mapped_column(
        ForeignKey(
            "roles.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    permission_id: Mapped[int] = mapped_column(
        ForeignKey(
            "permissions.id",
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