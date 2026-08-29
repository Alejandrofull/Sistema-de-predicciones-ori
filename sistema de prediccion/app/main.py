from fastapi import FastAPI

from app.api.routers.imports import router as imports_router
from app.api.routers.exports import router as exports_router
from app.api.routers.reports import router as reports_router

app = FastAPI(
title="ML Prediction Service"
)

app.include_router(imports_router, prefix="/api")
app.include_router(exports_router, prefix="/api")
app.include_router(reports_router, prefix="/api")

@app.get("/health", tags=["health"])
def health():
    return {
"status": "ok",
"service": "ml-prediction-service"
}
