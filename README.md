# Backend ML Architecture

FastAPI architecture for demand/time-series forecasting with training, model evaluation, notifications, JWT/RBAC security, audit traceability and a multi-source data ingestion pipeline.

## Supported data inputs

- CSV (`.csv`)
- Excel (`.xlsx`, `.xls`)
- JSON (`.json` or JSON payloads)
- Parquet (`.parquet`)
- SQL databases supported by SQLAlchemy (PostgreSQL, MySQL, SQL Server, SQLite, etc., with the corresponding driver)
- REST APIs returning JSON

## Prediction data flow

`source -> ingestion -> validation -> cleaning -> normalization/transformation -> feature engineering -> model -> prediction/evaluation`

All sources are converted to a common pandas DataFrame representation before entering `app/ml/features` and the prediction/training services.

## Main data modules

- `app/data/ingestion`: source-specific loaders and loader factory.
- `app/data/validation`: schema, columns, datatypes and quality checks.
- `app/data/preprocessing`: cleaning, missing values, dates, outliers and normalization.
- `app/data/transformers`: canonical transformation for prediction datasets.
- `app/api/routers/imports.py`: import-format API surface.
- `app/services/import_service.py`: orchestration layer between imports and ML.

## Minimum canonical dataset

For a univariate time-series model such as ARIMA, the minimum logical input is:

- a date/time column
- a numeric target column (e.g. demand, sales, quantity)

Tree-based and hybrid models may additionally use product/store identifiers, price, stock, promotions, holidays and other external variables. Feature engineering lives under `app/ml/features`.

## Run

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Exportación y reportes

El servicio incluye una capa de salida independiente para que otro backend pueda consumir resultados o descargar archivos.

### Exportaciones soportadas
- CSV
- Excel XLSX
- JSON
- Parquet
- Base de datos SQL (exportador interno)
- API/HTTP (exportador interno)

### Reportes soportados
- PDF
- Excel XLSX
- HTML

### Endpoints base
- `POST /api/v1/imports/file`
- `POST /api/v1/exports`
- `GET /api/v1/exports/{filename}`
- `POST /api/v1/reports`
- `GET /api/v1/reports/{filename}`
- `GET /health`

### Flujo previsto
`DB / CSV / Excel / JSON / API -> validación -> preprocesamiento -> features -> modelo -> predicción -> exportación / reporte / DB / API`

> Nota: esta entrega es una arquitectura base extensible. Los modelos ML y varios servicios originales continúan como esqueletos para implementar la lógica específica del proyecto.
