from __future__ import annotations

from io import BytesIO

import pandas as pd

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)

from sqlalchemy.orm import Session

from app.database.session import (
    get_db,
)

from app.schemas.inventory_import import (
    InventoryImportResponse,
)

from app.security.permissions import (
    Permissions,
    require_permission,
)

from app.services.audit_service import (
    AuditService,
)

from app.services.inventory_import_service import (
    InventoryImportService,
)


router = APIRouter(
    prefix="/inventory/imports",
    tags=["inventory-imports"]
)

service = InventoryImportService()


@router.post(
    "",
    response_model=(
        InventoryImportResponse
    )
)
async def import_inventory_file(
    file: UploadFile = File(...),

    phase: str = Form(...),

    business_series_id: int | None = Form(
        default=None
    ),

    date_column: str = Form(
        default="fecha"
    ),

    entity_column: str | None = Form(
        default="producto"
    ),

    opening_stock_column: str = Form(
        default="stock_inicial"
    ),

    replenishment_column: str = Form(
        default="reposicion"
    ),

    actual_demand_column: str = Form(
        default="demanda_real"
    ),

    closing_stock_column: str | None = Form(
        default="stock_final"
    ),

    predicted_demand_column: str | None = Form(
        default=None
    ),

    source_type: str = Form(
        default="import"
    ),

    auto_match_prediction: bool = Form(
        default=True
    ),

    sync_actual_values: bool = Form(
        default=True
    ),

    current_user=Depends(
        require_permission(
            Permissions.INVENTORY_IMPORT
        )
    ),

    db: Session = Depends(
        get_db
    )
):
    filename = (
        file.filename
        or "inventory"
    )

    extension = (
        filename
        .rsplit(
            ".",
            1
        )[-1]
        .lower()
        if "." in filename
        else ""
    )

    if extension not in {
        "csv",
        "xlsx",
        "xls",
    }:

        raise HTTPException(
            status_code=400,
            detail=(
                "Formato no soportado. "
                "Use CSV, XLSX o XLS."
            )
        )

    content = await file.read()

    if not content:

        raise HTTPException(
            status_code=400,
            detail=(
                "El archivo está vacío"
            )
        )

    try:

        dataframe = (
            _read_dataframe(
                content=content,
                extension=extension
            )
        )

    except Exception as error:

        raise HTTPException(
            status_code=400,
            detail=(
                "No se pudo leer "
                "el archivo: "
                f"{error}"
            )
        )

    result = (
        service.import_dataframe(
            db=db,
            dataframe=dataframe,
            filename=filename,
            user_id=current_user.id,
            phase=phase,
            business_series_id=(
                business_series_id
            ),
            date_column=(
                date_column
            ),
            entity_column=(
                entity_column
            ),
            opening_stock_column=(
                opening_stock_column
            ),
            replenishment_column=(
                replenishment_column
            ),
            actual_demand_column=(
                actual_demand_column
            ),
            closing_stock_column=(
                closing_stock_column
            ),
            predicted_demand_column=(
                predicted_demand_column
            ),
            source_type=(
                source_type
            ),
            auto_match_prediction=(
                auto_match_prediction
            ),
            sync_actual_values=(
                sync_actual_values
            )
        )
    )

    AuditService.log_safe(
        db=db,
        user_id=current_user.id,
        action="inventory.import",
        entity="inventory_observation",
        entity_id=None,
        details={
            "filename": (
                filename
            ),
            "file_format": (
                extension
            ),
            "rows_received": int(
                len(
                    dataframe
                )
            ),
            "phase": (
                phase
            ),
            "business_series_id": (
                business_series_id
            ),
            "source_type": (
                source_type
            ),
            "auto_match_prediction": (
                auto_match_prediction
            ),
            "sync_actual_values": (
                sync_actual_values
            ),
        }
    )

    return result


def _read_dataframe(
    content: bytes,
    extension: str
) -> pd.DataFrame:

    buffer = BytesIO(
        content
    )

    if extension == "csv":

        try:

            return pd.read_csv(
                buffer
            )

        except UnicodeDecodeError:

            buffer.seek(
                0
            )

            return pd.read_csv(
                buffer,
                encoding="latin-1"
            )

    if extension in {
        "xlsx",
        "xls",
    }:

        return pd.read_excel(
            buffer
        )

    raise ValueError(
        "Formato no soportado"
    )