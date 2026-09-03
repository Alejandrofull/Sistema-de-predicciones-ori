from datetime import datetime
from typing import Any

from pydantic import (
    BaseModel,
    Field,
    field_validator,
)


class BusinessSeriesCreateRequest(
    BaseModel
):
    external_entity_id: str = Field(
        ...,
        min_length=1,
        max_length=150
    )

    entity_type: str = Field(
        ...,
        min_length=1,
        max_length=50
    )

    name: str | None = Field(
        default=None,
        max_length=255
    )

    dimensions: dict[
        str,
        Any
    ] | None = None

    is_active: bool = True

    @field_validator(
        "external_entity_id"
    )
    @classmethod
    def normalize_external_id(
        cls,
        value: str
    ) -> str:

        value = value.strip()

        if not value:
            raise ValueError(
                "external_entity_id "
                "es obligatorio"
            )

        return value

    @field_validator(
        "entity_type"
    )
    @classmethod
    def normalize_entity_type(
        cls,
        value: str
    ) -> str:

        value = (
            value
            .strip()
            .lower()
        )

        if not value:
            raise ValueError(
                "entity_type "
                "es obligatorio"
            )

        return value

    @field_validator(
        "name"
    )
    @classmethod
    def normalize_name(
        cls,
        value: str | None
    ) -> str | None:

        if value is None:
            return None

        value = value.strip()

        return (
            value
            if value
            else None
        )


class BusinessSeriesUpdateRequest(
    BaseModel
):
    external_entity_id: str = Field(
        ...,
        min_length=1,
        max_length=150
    )

    entity_type: str = Field(
        ...,
        min_length=1,
        max_length=50
    )

    name: str | None = Field(
        default=None,
        max_length=255
    )

    dimensions: dict[
        str,
        Any
    ] | None = None

    is_active: bool = True

    @field_validator(
        "external_entity_id"
    )
    @classmethod
    def normalize_external_id(
        cls,
        value: str
    ) -> str:

        value = value.strip()

        if not value:
            raise ValueError(
                "external_entity_id "
                "es obligatorio"
            )

        return value

    @field_validator(
        "entity_type"
    )
    @classmethod
    def normalize_entity_type(
        cls,
        value: str
    ) -> str:

        value = (
            value
            .strip()
            .lower()
        )

        if not value:
            raise ValueError(
                "entity_type "
                "es obligatorio"
            )

        return value

    @field_validator(
        "name"
    )
    @classmethod
    def normalize_name(
        cls,
        value: str | None
    ) -> str | None:

        if value is None:
            return None

        value = value.strip()

        return (
            value
            if value
            else None
        )


class BusinessSeriesStatusRequest(
    BaseModel
):
    is_active: bool


class BusinessSeriesResponse(
    BaseModel
):
    id: int

    external_entity_id: str

    entity_type: str

    name: str | None

    dimensions: dict[
        str,
        Any
    ] | None

    is_active: bool

    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class BusinessSeriesDeleteResponse(
    BaseModel
):
    message: str