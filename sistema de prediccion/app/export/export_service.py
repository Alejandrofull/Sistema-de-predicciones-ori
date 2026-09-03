from pathlib import Path

import pandas as pd


class ExportService:

    def __init__(
        self,
        base_dir: Path | None = None
    ):
        self.base_dir = (
            Path(base_dir)
            if base_dir
            else Path("storage/exports")
        )

    def export_dataframe(
        self,
        dataframe: pd.DataFrame,
        export_format: str,
        filename: str,
        base_dir: Path | None = None
    ) -> Path:

        if dataframe is None:
            raise ValueError(
                "El DataFrame no puede ser None"
            )

        if dataframe.empty:
            raise ValueError(
                "No hay datos para exportar"
            )

        export_format = (
            export_format
            .lower()
            .strip()
        )

        filename = (
            filename
            .strip()
        )

        if not filename:
            raise ValueError(
                "El nombre del archivo es obligatorio"
            )

        output_dir = (
            Path(base_dir)
            if base_dir
            else self.base_dir
        )

        output_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        if export_format == "csv":

            path = (
                output_dir
                / f"{filename}.csv"
            )

            dataframe.to_csv(
                path,
                index=False,
                encoding="utf-8-sig"
            )

        elif export_format in {
            "xlsx",
            "excel"
        }:

            path = (
                output_dir
                / f"{filename}.xlsx"
            )

            dataframe.to_excel(
                path,
                index=False,
                engine="openpyxl"
            )

        elif export_format == "json":

            path = (
                output_dir
                / f"{filename}.json"
            )

            dataframe.to_json(
                path,
                orient="records",
                force_ascii=False,
                indent=2,
                date_format="iso"
            )

        elif export_format == "parquet":

            path = (
                output_dir
                / f"{filename}.parquet"
            )

            dataframe.to_parquet(
                path,
                index=False
            )

        else:
            raise ValueError(
                f"Formato de exportación no soportado: "
                f"{export_format}"
            )

        if not path.exists():
            raise RuntimeError(
                "No se pudo generar el archivo"
            )

        return path