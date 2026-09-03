from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

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

    session_id: Mapped[int] = mapped_column(
        ForeignKey(
            "user_sessions.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    jti: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True
    )

    token_hash: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True
    )

    revoked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True
    )

    revoked_reason: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    replaced_by_jti: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )