from datetime import datetime

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)

from sqlalchemy.orm import Session

from app.database.session import (
    get_db,
)

from app.repositories.dataset_external_variable_repository import (
    DatasetExternalVariableRepository,
)

from app.repositories.external_variable_repository import (
    ExternalVariableRepository,
)

from app.repositories.external_variable_value_repository import (
    ExternalVariableValueRepository,
)

from app.schemas.external_variable import (
    DatasetExternalVariableResponse,
    ExternalVariableCreateRequest,
    ExternalVariableDeleteResponse,
    ExternalVariableResponse,
    ExternalVariableStatusRequest,
    ExternalVariableUpdateRequest,
    ExternalVariableValueBulkRequest,
    ExternalVariableValueRequest,
    ExternalVariableValueResponse,
)

from app.security.permissions import (
    Permissions,
    require_permission,
)

from app.services.audit_service import (
    AuditService,
)

from app.services.dataset_external_variable_service import (
    DatasetExternalVariableService,
)

from app.services.external_variable_service import (
    ExternalVariableService,
)


router = APIRouter(
    prefix="/external-variables",
    tags=["external-variables"]
)


dataset_router = APIRouter(
    prefix="/datasets",
    tags=["dataset-external-variables"]
)


# ==========================================
# VARIABLES
# ==========================================

@router.post(
    "",
    response_model=(
        ExternalVariableResponse
    ),
    status_code=201
)
def create_external_variable(
    payload: ExternalVariableCreateRequest,

    current_user=Depends(
        require_permission(
            Permissions.EXTERNAL_VARIABLES_MANAGE
        )
    ),

    db: Session = Depends(
        get_db
    )
):
    variable = (
        ExternalVariableService
        .create_variable(
            db=db,
            name=payload.name,
            variable_type=(
                payload.variable_type
            ),
            source_type=(
                payload.source_type
            ),
            description=(
                payload.description
            ),
            unit=payload.unit,
            is_active=(
                payload.is_active
            )
        )
    )

    AuditService.log_safe(
        db=db,
        user_id=current_user.id,
        action="external_variable.create",
        entity="external_variable",
        entity_id=variable.id,
        details={
            "name": (
                variable.name
            ),
            "variable_type": (
                variable.variable_type
            ),
            "source_type": (
                variable.source_type
            ),
            "unit": (
                variable.unit
            ),
            "is_active": (
                variable.is_active
            ),
        }
    )

    return variable


@router.get(
    "",
    response_model=list[
        ExternalVariableResponse
    ]
)
def get_external_variables(
    include_inactive: bool = Query(
        default=False
    ),

    current_user=Depends(
        require_permission(
            Permissions.EXTERNAL_VARIABLES_VIEW
        )
    ),

    db: Session = Depends(
        get_db
    )
):
    return (
        ExternalVariableRepository
        .get_all(
            db=db,
            include_inactive=(
                include_inactive
            )
        )
    )


@router.get(
    "/{variable_id}",
    response_model=(
        ExternalVariableResponse
    )
)
def get_external_variable(
    variable_id: int,

    current_user=Depends(
        require_permission(
            Permissions.EXTERNAL_VARIABLES_VIEW
        )
    ),

    db: Session = Depends(
        get_db
    )
):
    variable = (
        ExternalVariableRepository
        .get_by_id(
            db,
            variable_id
        )
    )

    if not variable:

        raise HTTPException(
            status_code=404,
            detail=(
                "Variable externa "
                "no encontrada"
            )
        )

    return variable


@router.put(
    "/{variable_id}",
    response_model=(
        ExternalVariableResponse
    )
)
def update_external_variable(
    variable_id: int,
    payload: ExternalVariableUpdateRequest,

    current_user=Depends(
        require_permission(
            Permissions.EXTERNAL_VARIABLES_MANAGE
        )
    ),

    db: Session = Depends(
        get_db
    )
):
    variable = (
        ExternalVariableService
        .update_variable(
            db=db,
            variable_id=variable_id,
            name=payload.name,
            variable_type=(
                payload.variable_type
            ),
            source_type=(
                payload.source_type
            ),
            description=(
                payload.description
            ),
            unit=payload.unit,
            is_active=(
                payload.is_active
            )
        )
    )

    AuditService.log_safe(
        db=db,
        user_id=current_user.id,
        action="external_variable.update",
        entity="external_variable",
        entity_id=variable_id,
        details={
            "name": (
                payload.name
            ),
            "variable_type": (
                payload.variable_type
            ),
            "source_type": (
                payload.source_type
            ),
            "description": (
                payload.description
            ),
            "unit": (
                payload.unit
            ),
            "is_active": (
                payload.is_active
            ),
        }
    )

    return variable


@router.patch(
    "/{variable_id}/status",
    response_model=(
        ExternalVariableResponse
    )
)
def set_external_variable_status(
    variable_id: int,
    payload: ExternalVariableStatusRequest,

    current_user=Depends(
        require_permission(
            Permissions.EXTERNAL_VARIABLES_MANAGE
        )
    ),

    db: Session = Depends(
        get_db
    )
):
    variable = (
        ExternalVariableService.set_status(
            db=db,
            variable_id=variable_id,
            is_active=(
                payload.is_active
            )
        )
    )

    AuditService.log_safe(
        db=db,
        user_id=current_user.id,
        action=(
            "external_variable.status.update"
        ),
        entity="external_variable",
        entity_id=variable_id,
        details={
            "is_active": (
                payload.is_active
            )
        }
    )

    return variable


# ==========================================
# VALUES
# ==========================================

@router.post(
    "/{variable_id}/values",
    response_model=(
        ExternalVariableValueResponse
    ),
    status_code=201
)
def create_external_variable_value(
    variable_id: int,
    payload: ExternalVariableValueRequest,

    current_user=Depends(
        require_permission(
            Permissions.EXTERNAL_VARIABLES_MANAGE
        )
    ),

    db: Session = Depends(
        get_db
    )
):
    value = (
        ExternalVariableService.create_value(
            db=db,
            variable_id=variable_id,
            reference_date=(
                payload.reference_date
            ),
            numeric_value=(
                payload.numeric_value
            ),
            text_value=(
                payload.text_value
            ),
            business_key=(
                payload.business_key
            )
        )
    )

    AuditService.log_safe(
        db=db,
        user_id=current_user.id,
        action="external_variable.value.create",
        entity="external_variable_value",
        entity_id=value.id,
        details={
            "variable_id": (
                variable_id
            ),
            "reference_date": (
                payload.reference_date
            ),
            "numeric_value": (
                payload.numeric_value
            ),
            "text_value": (
                payload.text_value
            ),
            "business_key": (
                payload.business_key
            ),
        }
    )

    return value


@router.post(
    "/{variable_id}/values/bulk",
    response_model=list[
        ExternalVariableValueResponse
    ],
    status_code=201
)
def create_external_variable_values_bulk(
    variable_id: int,
    payload: ExternalVariableValueBulkRequest,

    current_user=Depends(
        require_permission(
            Permissions.EXTERNAL_VARIABLES_MANAGE
        )
    ),

    db: Session = Depends(
        get_db
    )
):
    values = (
        ExternalVariableService.create_values(
            db=db,
            variable_id=variable_id,
            values=payload.values
        )
    )

    AuditService.log_safe(
        db=db,
        user_id=current_user.id,
        action=(
            "external_variable.values.bulk_create"
        ),
        entity="external_variable",
        entity_id=variable_id,
        details={
            "variable_id": (
                variable_id
            ),
            "records_requested": (
                len(
                    payload.values
                )
            ),
            "records_created": (
                len(
                    values
                )
            ),
        }
    )

    return values


@router.get(
    "/{variable_id}/values",
    response_model=list[
        ExternalVariableValueResponse
    ]
)
def get_external_variable_values(
    variable_id: int,

    start_date: datetime | None = Query(
        default=None
    ),

    end_date: datetime | None = Query(
        default=None
    ),

    business_key: str | None = Query(
        default=None
    ),

    current_user=Depends(
        require_permission(
            Permissions.EXTERNAL_VARIABLES_VIEW
        )
    ),

    db: Session = Depends(
        get_db
    )
):
    variable = (
        ExternalVariableRepository.get_by_id(
            db,
            variable_id
        )
    )

    if not variable:

        raise HTTPException(
            status_code=404,
            detail=(
                "Variable externa "
                "no encontrada"
            )
        )

    return (
        ExternalVariableValueRepository
        .get_by_variable(
            db=db,
            variable_id=variable_id,
            start_date=start_date,
            end_date=end_date,
            business_key=business_key,
            include_global=True
        )
    )


@router.delete(
    "/{variable_id}/values/{value_id}",
    response_model=(
        ExternalVariableDeleteResponse
    )
)
def delete_external_variable_value(
    variable_id: int,
    value_id: int,

    current_user=Depends(
        require_permission(
            Permissions.EXTERNAL_VARIABLES_MANAGE
        )
    ),

    db: Session = Depends(
        get_db
    )
):
    value = (
        ExternalVariableValueRepository
        .get_by_id(
            db,
            value_id
        )
    )

    if (
        not value
        or value.variable_id
        != variable_id
    ):

        raise HTTPException(
            status_code=404,
            detail=(
                "Valor de variable externa "
                "no encontrado"
            )
        )

    details = {
        "variable_id": (
            value.variable_id
        ),
        "reference_date": (
            value.reference_date
        ),
        "numeric_value": (
            value.numeric_value
        ),
        "text_value": (
            value.text_value
        ),
        "business_key": (
            value.business_key
        ),
    }

    ExternalVariableValueRepository.delete(
        db=db,
        value=value
    )

    AuditService.log_safe(
        db=db,
        user_id=current_user.id,
        action="external_variable.value.delete",
        entity="external_variable_value",
        entity_id=value_id,
        details=details
    )

    return {
        "message": (
            "Valor eliminado correctamente"
        )
    }


# ==========================================
# DATASET ASSOCIATIONS
# ==========================================

@dataset_router.post(
    "/{dataset_id}/external-variables/"
    "{variable_id}",
    response_model=(
        DatasetExternalVariableResponse
    )
)
def attach_external_variable(
    dataset_id: int,
    variable_id: int,

    current_user=Depends(
        require_permission(
            Permissions.EXTERNAL_VARIABLES_MANAGE
        )
    ),

    db: Session = Depends(
        get_db
    )
):
    DatasetExternalVariableService.attach_variable(
        db=db,
        dataset_id=dataset_id,
        variable_id=variable_id,
        user_id=current_user.id
    )

    variable = (
        ExternalVariableRepository.get_by_id(
            db,
            variable_id
        )
    )

    AuditService.log_safe(
        db=db,
        user_id=current_user.id,
        action=(
            "dataset.external_variable.attach"
        ),
        entity="dataset",
        entity_id=dataset_id,
        details={
            "dataset_id": (
                dataset_id
            ),
            "external_variable_id": (
                variable_id
            ),
            "external_variable_name": (
                variable.name
                if variable
                else None
            ),
        }
    )

    return {
        "dataset_id": dataset_id,
        "external_variable": variable
    }


@dataset_router.get(
    "/{dataset_id}/external-variables",
    response_model=list[
        ExternalVariableResponse
    ]
)
def get_dataset_external_variables(
    dataset_id: int,

    current_user=Depends(
        require_permission(
            Permissions.EXTERNAL_VARIABLES_VIEW
        )
    ),

    db: Session = Depends(
        get_db
    )
):
    return (
        DatasetExternalVariableRepository
        .get_variables_by_dataset(
            db=db,
            dataset_id=dataset_id
        )
    )


@dataset_router.delete(
    "/{dataset_id}/external-variables/"
    "{variable_id}",
    response_model=(
        ExternalVariableDeleteResponse
    )
)
def detach_external_variable(
    dataset_id: int,
    variable_id: int,

    current_user=Depends(
        require_permission(
            Permissions.EXTERNAL_VARIABLES_MANAGE
        )
    ),

    db: Session = Depends(
        get_db
    )
):
    DatasetExternalVariableService.detach_variable(
        db=db,
        dataset_id=dataset_id,
        variable_id=variable_id,
        user_id=current_user.id
    )

    AuditService.log_safe(
        db=db,
        user_id=current_user.id,
        action=(
            "dataset.external_variable.detach"
        ),
        entity="dataset",
        entity_id=dataset_id,
        details={
            "dataset_id": (
                dataset_id
            ),
            "external_variable_id": (
                variable_id
            ),
        }
    )

    return {
        "message": (
            "Variable externa desvinculada "
            "correctamente"
        )
    }