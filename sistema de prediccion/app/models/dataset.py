from datetime import (
    datetime,
    timezone,
)

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from app.database.base import Base


class Dataset(Base):
    __tablename__ = "datasets"

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

    parent_dataset_id: Mapped[int | None] = mapped_column(
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

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True
    )

    original_filename: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    file_format: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
        index=True
    )

    source_type: Mapped[str] = mapped_column(
        String(30),
        default="file",
        nullable=False,
        index=True
    )

    processing_stage: Mapped[str] = mapped_column(
        String(30),
        default="raw",
        nullable=False,
        index=True
    )

    storage_path: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        unique=True
    )

    row_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    column_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    columns_info: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True
    )

    quality_report: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True
    )

    dataset_metadata: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="ready",
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

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(
            timezone.utc
        ),
        onupdate=lambda: datetime.now(
            timezone.utc
        ),
        nullable=False
    )