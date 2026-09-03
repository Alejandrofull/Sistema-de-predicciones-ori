from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class DatasetExternalVariable(Base):
    __tablename__ = "dataset_external_variables"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    dataset_id: Mapped[int] = mapped_column(
        ForeignKey(
            "datasets.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    external_variable_id: Mapped[int] = mapped_column(
        ForeignKey(
            "external_variables.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )