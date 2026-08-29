from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from .base import BaseReportGenerator


class PDFReportGenerator(BaseReportGenerator):
    def generate(self, context: dict, destination: Path) -> Path:
        destination.parent.mkdir(parents=True, exist_ok=True)
        c = canvas.Canvas(str(destination), pagesize=A4)
        width, height = A4
        y = height - 60
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, y, str(context.get("title", "Reporte de predicción"))[:90])
        y -= 30
        c.setFont("Helvetica", 10)
        summary = str(context.get("summary", ""))
        for line in [summary[i:i+100] for i in range(0, len(summary), 100)] or [""]:
            c.drawString(50, y, line)
            y -= 15
        y -= 10
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "Métricas")
        y -= 20
        c.setFont("Helvetica", 10)
        for key, value in context.get("metrics", {}).items():
            if y < 60:
                c.showPage(); y = height - 60; c.setFont("Helvetica", 10)
            c.drawString(60, y, f"{key}: {value}")
            y -= 15
        c.save()
        return destination
