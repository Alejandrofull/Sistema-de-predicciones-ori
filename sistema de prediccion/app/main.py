import os

from contextlib import (
    asynccontextmanager,
)

from fastapi import (
    FastAPI,
    status,
)

from fastapi.middleware.cors import CORSMiddleware

from fastapi.responses import (
    JSONResponse,
)

from app.api.routers.anomalies import (
    router as anomalies_router,
)

from app.api.routers.audit import (
    router as audit_router,
)

from app.api.routers.auth import (
    router as auth_router,
)

from app.api.routers.business_series import (
    router as business_series_router,
)

from app.api.routers.dataset_processing import (
    router as dataset_processing_router,
)

from app.api.routers.dataset_validation import (
    router as dataset_validation_router,
)

from app.api.routers.datasets import (
    router as datasets_router,
)

from app.api.routers.exports import (
    router as exports_router,
)

from app.api.routers.external_variables import (
    dataset_router
    as dataset_external_variables_router,
)

from app.api.routers.external_variables import (
    router as external_variables_router,
)

from app.api.routers.imports import (
    router as imports_router,
)

from app.api.routers.inventory import (
    router as inventory_router,
)

from app.api.routers.inventory_imports import (
    router as inventory_imports_router,
)

from app.api.routers.kpis import (
    router as kpis_router,
)

from app.api.routers.models import (
    router as models_router,
)

from app.api.routers.monitoring import (
    router as monitoring_router,
)

from app.api.routers.notifications import (
    router as notifications_router,
)

from app.api.routers.predictions import (
    router as predictions_router,
)

from app.api.routers.reports import (
    router as reports_router,
)

from app.api.routers.retraining import (
    router as retraining_router,
)

from app.api.routers.roles import (
    router as roles_router,
)

from app.api.routers.series_extraction import (
    router as series_extraction_router,
)

from app.api.routers.statistics import (
    router as statistics_router,
)

from app.api.routers.trainings import (
    router as trainings_router,
)

from app.api.routers.users import (
    router as users_router,
)

from app.integrations.supabase.database import (
    test_database_connection,
)


# ==========================================
# LIFESPAN
# ==========================================

@asynccontextmanager
async def lifespan(
    app: FastAPI
):
    try:

        database = (
            test_database_connection()
        )

        print(
            "✅ Base de datos "
            "conectada correctamente"
        )

        print(
            f"   Database: "
            f"{database['database']}"
        )

        print(
            f"   User: "
            f"{database['user']}"
        )

        print(
            f"   Server time: "
            f"{database['server_time']}"
        )

    except Exception as error:

        print(
            "❌ Error de conexión "
            "con la base de datos"
        )

        print(
            f"   {error}"
        )

        # El sistema depende de PostgreSQL.
        # Si la conexión falla durante el
        # arranque, la aplicación no debe
        # continuar operando parcialmente.
        raise

    yield


# ==========================================
# FASTAPI
# ==========================================

app = FastAPI(
    title="ML Prediction Service",
    description=(
        "Servicio de predicción de demanda, "
        "gestión de modelos de Machine Learning "
        "y soporte a la gestión de inventarios."
    ),
    lifespan=lifespan
)


# ==========================================
# CORS
# ==========================================
# Los orígenes permitidos se leen desde la
# variable de entorno CORS_ORIGINS, separados
# por comas. Así se puede tener una config
# distinta en local, staging y producción sin
# tocar el código.
#
# Ejemplo en .env (desarrollo):
#   CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
#
# Ejemplo en producción (Render, etc.):
#   CORS_ORIGINS=https://tu-frontend.vercel.app,https://tu-dominio.com

cors_origins_env = os.getenv("CORS_ORIGINS", "")

cors_origins = [
    origin.strip()
    for origin in cors_origins_env.split(",")
    if origin.strip()
]

if not cors_origins:
    # Fallback de desarrollo si no se define la variable.
    cors_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# AUTH / RBAC
# ==========================================

app.include_router(
    auth_router,
    prefix="/api"
)

app.include_router(
    users_router,
    prefix="/api"
)

app.include_router(
    roles_router,
    prefix="/api"
)


# ==========================================
# BUSINESS SERIES
# ==========================================

app.include_router(
    business_series_router,
    prefix="/api"
)


# ==========================================
# DATASETS
# ==========================================

app.include_router(
    datasets_router,
    prefix="/api"
)

app.include_router(
    dataset_validation_router,
    prefix="/api"
)

app.include_router(
    dataset_processing_router,
    prefix="/api"
)

app.include_router(
    series_extraction_router,
    prefix="/api"
)

app.include_router(
    imports_router,
    prefix="/api"
)

app.include_router(
    dataset_external_variables_router,
    prefix="/api"
)


# ==========================================
# EXTERNAL VARIABLES
# ==========================================

app.include_router(
    external_variables_router,
    prefix="/api"
)


# ==========================================
# MACHINE LEARNING
# ==========================================

app.include_router(
    trainings_router,
    prefix="/api"
)

app.include_router(
    models_router,
    prefix="/api"
)

app.include_router(
    predictions_router,
    prefix="/api"
)

app.include_router(
    monitoring_router,
    prefix="/api"
)

app.include_router(
    retraining_router,
    prefix="/api"
)

app.include_router(
    anomalies_router,
    prefix="/api"
)


# ==========================================
# INVENTORY
# ==========================================

app.include_router(
    inventory_router,
    prefix="/api"
)

app.include_router(
    inventory_imports_router,
    prefix="/api"
)


# ==========================================
# KPIS
# ==========================================

app.include_router(
    kpis_router,
    prefix="/api"
)


# ==========================================
# STATISTICS
# ==========================================

app.include_router(
    statistics_router,
    prefix="/api"
)


# ==========================================
# NOTIFICATIONS
# ==========================================

app.include_router(
    notifications_router,
    prefix="/api"
)


# ==========================================
# AUDIT
# ==========================================

app.include_router(
    audit_router,
    prefix="/api"
)


# ==========================================
# EXPORTS / REPORTS
# ==========================================

app.include_router(
    exports_router,
    prefix="/api"
)

app.include_router(
    reports_router,
    prefix="/api"
)


# ==========================================
# HEALTH
# ==========================================

@app.get(
    "/health",
    tags=["health"]
)
def health():

    try:

        database = (
            test_database_connection()
        )

        return {
            "status": "ok",
            "service": (
                "ml-prediction-service"
            ),
            "database": {
                "status": (
                    "connected"
                ),
                **database
            }
        }

    except Exception as error:

        return JSONResponse(
            status_code=(
                status
                .HTTP_503_SERVICE_UNAVAILABLE
            ),
            content={
                "status": "error",
                "service": (
                    "ml-prediction-service"
                ),
                "database": {
                    "status": (
                        "disconnected"
                    ),
                    "error": str(
                        error
                    )
                }
            }
        )