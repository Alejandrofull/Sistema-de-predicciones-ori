from sqlalchemy import (
    select,
)

from sqlalchemy.orm import Session

from app.models.dataset import Dataset


class DatasetRepository:

    @staticmethod
    def create(
        db: Session,
        user_id: int | None,
        name: str,
        original_filename: str | None,
        file_format: str | None,
        source_type: str,
        storage_path: str | None,
        row_count: int,
        column_count: int,
        columns_info: list | None,
        quality_report: dict | None,
        dataset_metadata: dict | None = None,
        status: str = "ready",
        parent_dataset_id: int | None = None,
        processing_stage: str = "raw",
        business_series_id: int | None = None
    ) -> Dataset:

        dataset = Dataset(
            user_id=user_id,
            parent_dataset_id=parent_dataset_id,
            business_series_id=business_series_id,
            name=name,
            original_filename=original_filename,
            file_format=file_format,
            source_type=source_type,
            processing_stage=processing_stage,
            storage_path=storage_path,
            row_count=row_count,
            column_count=column_count,
            columns_info=columns_info,
            quality_report=quality_report,
            dataset_metadata=dataset_metadata,
            status=status
        )

        db.add(dataset)
        db.commit()
        db.refresh(dataset)

        return dataset

    @staticmethod
    def get_by_id(
        db: Session,
        dataset_id: int
    ) -> Dataset | None:

        return db.get(
            Dataset,
            dataset_id
        )

    @staticmethod
    def get_by_user(
        db: Session,
        user_id: int
    ) -> list[Dataset]:

        statement = (
            select(Dataset)
            .where(
                Dataset.user_id
                == user_id
            )
            .order_by(
                Dataset.created_at.desc()
            )
        )

        return list(
            db.scalars(
                statement
            ).all()
        )

    @staticmethod
    def get_by_business_series(
        db: Session,
        business_series_id: int
    ) -> list[Dataset]:

        statement = (
            select(Dataset)
            .where(
                Dataset.business_series_id
                == business_series_id
            )
            .order_by(
                Dataset.created_at.desc()
            )
        )

        return list(
            db.scalars(
                statement
            ).all()
        )

    @staticmethod
    def get_latest_by_business_series(
        db: Session,
        business_series_id: int,
        processing_stage: str | None = None
    ) -> Dataset | None:

        statement = (
            select(Dataset)
            .where(
                Dataset.business_series_id
                == business_series_id
            )
        )

        if processing_stage:
            statement = (
                statement.where(
                    Dataset.processing_stage
                    == processing_stage
                )
            )

        statement = (
            statement
            .order_by(
                Dataset.created_at.desc()
            )
            .limit(1)
        )

        return db.scalar(
            statement
        )

    @staticmethod
    def get_children(
        db: Session,
        parent_dataset_id: int
    ) -> list[Dataset]:

        statement = (
            select(Dataset)
            .where(
                Dataset.parent_dataset_id
                == parent_dataset_id
            )
            .order_by(
                Dataset.created_at.desc()
            )
        )

        return list(
            db.scalars(
                statement
            ).all()
        )

    @staticmethod
    def get_all(
        db: Session
    ) -> list[Dataset]:

        statement = (
            select(Dataset)
            .order_by(
                Dataset.created_at.desc()
            )
        )

        return list(
            db.scalars(
                statement
            ).all()
        )

    @staticmethod
    def update_status(
        db: Session,
        dataset: Dataset,
        status: str
    ) -> Dataset:

        dataset.status = status

        db.commit()
        db.refresh(dataset)

        return dataset

    @staticmethod
    def update_metadata(
        db: Session,
        dataset: Dataset,
        metadata: dict
    ) -> Dataset:

        dataset.dataset_metadata = metadata

        db.commit()
        db.refresh(dataset)

        return dataset

    @staticmethod
    def delete(
        db: Session,
        dataset: Dataset
    ) -> None:

        db.delete(
            dataset
        )

        db.commit()