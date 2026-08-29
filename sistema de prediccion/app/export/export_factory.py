from .exporters.csv_exporter import CSVExporter
from .exporters.excel_exporter import ExcelExporter
from .exporters.json_exporter import JSONExporter
from .exporters.parquet_exporter import ParquetExporter


EXPORTERS = {
    "csv": CSVExporter,
    "xlsx": ExcelExporter,
    "excel": ExcelExporter,
    "json": JSONExporter,
    "parquet": ParquetExporter,
}


def get_exporter(export_format: str):
    key = export_format.lower().lstrip(".")
    if key not in EXPORTERS:
        raise ValueError(f"Formato de exportación no soportado: {export_format}")
    return EXPORTERS[key]()
