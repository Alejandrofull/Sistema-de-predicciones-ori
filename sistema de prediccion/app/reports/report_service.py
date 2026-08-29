from pathlib import Path
from uuid import uuid4
from .generators.html_report import HTMLReportGenerator
from .generators.pdf_report import PDFReportGenerator
from .generators.excel_report import ExcelReportGenerator


GENERATORS = {
    "html": (HTMLReportGenerator, ".html"),
    "pdf": (PDFReportGenerator, ".pdf"),
    "xlsx": (ExcelReportGenerator, ".xlsx"),
    "excel": (ExcelReportGenerator, ".xlsx"),
}


class ReportService:
    def __init__(self, base_dir: str = "storage/reports"):
        self.base_dir = Path(base_dir)

    def generate(self, context: dict, report_format: str = "pdf", filename: str | None = None) -> Path:
        key = report_format.lower().lstrip(".")
        if key not in GENERATORS:
            raise ValueError(f"Formato de reporte no soportado: {report_format}")
        generator_cls, extension = GENERATORS[key]
        stem = filename or f"report_{uuid4().hex}"
        return generator_cls().generate(context, self.base_dir / f"{stem}{extension}")
