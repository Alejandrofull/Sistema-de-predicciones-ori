from pathlib import Path
import pandas as pd
from .base import BaseReportGenerator


class ExcelReportGenerator(BaseReportGenerator):
    def generate(self, context: dict, destination: Path) -> Path:
        destination.parent.mkdir(parents=True, exist_ok=True)
        metrics = pd.DataFrame(list(context.get("metrics", {}).items()), columns=["Métrica", "Valor"])
        predictions = pd.DataFrame(context.get("predictions", []))
        with pd.ExcelWriter(destination, engine="openpyxl") as writer:
            metrics.to_excel(writer, sheet_name="Resumen", index=False)
            if not predictions.empty:
                predictions.to_excel(writer, sheet_name="Predicciones", index=False)
        return destination
