from html import escape
from pathlib import Path
from .base import BaseReportGenerator


class HTMLReportGenerator(BaseReportGenerator):
    def generate(self, context: dict, destination: Path) -> Path:
        destination.parent.mkdir(parents=True, exist_ok=True)
        title = escape(str(context.get("title", "Reporte de predicción")))
        metrics = context.get("metrics", {})
        rows = "".join(
            f"<tr><th>{escape(str(k))}</th><td>{escape(str(v))}</td></tr>"
            for k, v in metrics.items()
        )
        html = f"""<!doctype html>
<html lang='es'><head><meta charset='utf-8'><title>{title}</title>
<style>body{{font-family:Arial,sans-serif;margin:40px}}table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #ddd;padding:8px;text-align:left}}th{{background:#f3f3f3}}</style></head>
<body><h1>{title}</h1><p>{escape(str(context.get('summary', '')))}</p><h2>Métricas</h2><table>{rows}</table></body></html>"""
        destination.write_text(html, encoding="utf-8")
        return destination
