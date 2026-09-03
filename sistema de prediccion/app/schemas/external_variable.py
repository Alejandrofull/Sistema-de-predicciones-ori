from datetime import datetime

from pydantic import (
    BaseModel,
    Field,
    field_validator,
    model_validator,
)


ALLOWED_VARIABLE_TYPES = {
    "numeric",
    "boolean",
    "categorical",
    "text",
}


class ExternalVariableCreateRequest(
    BaseModel
):
    name: str = Field(
        ...,
        min_length=1,
        max_length=100
    )

    variable_type: str = Field(
        ...,
        min_length=1,
        max_length=50
    )

    source_type: str = Field(
        ...,
        min_length=1,
        max_length=50
    )

    description: str | None = None

    unit: str | None = Field(
        default=None,
        max_length=50
    )

    is_active: bool = True

    @field_validator("name")
    @classmethod
    def normalize_name(
        cls,
        value: str
    ) -> str:

        value = value.strip()

        if not value:
            raise ValueError(
                "name es obligatorio"
            )

        return value

    @field_validator(
        "variable_type"
    )
    @classmethod
    def validate_variable_type(
        cls,
        value: str
    ) -> str:

        value = (
            value
            .strip()
            .lower()
        )

        if value not in (
            ALLOWED_VARIABLE_TYPES
        ):
            raise ValueError(
                "variable_type debe ser: "
                "numeric, boolean, "
                "categorical o text"
            )

        return value

    @field_validator(
        "source_type"
    )
    @classmethod
    def normalize_source_type(
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
                "source_type es obligatorio"
            )

        return value


class ExternalVariableUpdateRequest(
    ExternalVariableCreateRequest
):
    pass


class ExternalVariableStatusRequest(
    BaseModel
):
    is_active: bool


class ExternalVariableResponse(
    BaseModel
):
    id: int

    name: str

    variable_type: str

    source_type: str

    description: str | None

    unit: str | None

    is_active: bool

    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class ExternalVariableValueRequest(
    BaseModel
):
    reference_date: datetime

    numeric_value: float | None = None

    text_value: str | None = Field(
        default=None,
        max_length=255
    )

    business_key: str | None = Field(
        default=None,
        max_length=150
    )

    @model_validator(
        mode="after"
    )
    def validate_value(
        self
    ):
        if (
            self.numeric_value is None
            and self.text_value is None
        ):
            raise ValueError(
                "Debe proporcionar "
                "numeric_value o text_value"
            )

        if self.business_key:

            self.business_key = (
                self.business_key.strip()
                or None
            )

        return self


class ExternalVariableValueBulkRequest(
    BaseModel
):
    values: list[
        ExternalVariableValueRequest
    ] = Field(
        ...,
        min_length=1
    )


class ExternalVariableValueResponse(
    BaseModel
):
    id: int

    variable_id: int

    reference_date: datetime

    numeric_value: float | None

    text_value: str | None

    business_key: str | None

    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class DatasetExternalVariableResponse(
    BaseModel
):
    dataset_id: int

    external_variable: (
        ExternalVariableResponse
    )


class ExternalVariableDeleteResponse(
    BaseModel
):
    message: str