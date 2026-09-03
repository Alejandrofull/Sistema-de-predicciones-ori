import json

from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    ParagraphStyle,
    getSampleStyleSheet
)
from reportlab.lib.units import cm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle
)


class ReportService:

    def __init__(
        self,
        base_dir: Path | None = None
    ):
        self.base_dir = (
            Path(base_dir)
            if base_dir
            else Path("storage/reports")
        )

    def generate(
        self,
        context: dict[str, Any],
        report_format: str,
        filename: str,
        base_dir: Path | None = None
    ) -> Path:

        report_format = (
            report_format
            .lower()
            .strip()
        )

        filename = (
            filename
            .strip()
        )

        if not filename:
            raise ValueError(
                "El nombre del reporte es obligatorio"
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

        if report_format == "pdf":

            path = (
                output_dir
                / f"{filename}.pdf"
            )

            self._generate_pdf(
                context=context,
                path=path
            )

        elif report_format == "html":

            path = (
                output_dir
                / f"{filename}.html"
            )

            self._generate_html(
                context=context,
                path=path
            )

        elif report_format == "json":

            path = (
                output_dir
                / f"{filename}.json"
            )

            self._generate_json(
                context=context,
                path=path
            )

        else:
            raise ValueError(
                f"Formato de reporte no soportado: "
                f"{report_format}"
            )

        if not path.exists():
            raise RuntimeError(
                "No se pudo generar el reporte"
            )

        return path

    def _generate_pdf(
        self,
        context: dict[str, Any],
        path: Path
    ) -> None:

        document = SimpleDocTemplate(
            str(path),
            pagesize=A4,
            rightMargin=2 * cm,
            leftMargin=2 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm
        )

        styles = getSampleStyleSheet()

        title_style = styles[
            "Title"
        ]

        heading_style = styles[
            "Heading2"
        ]

        normal_style = styles[
            "BodyText"
        ]

        small_style = ParagraphStyle(
            "Small",
            parent=normal_style,
            fontSize=8,
            leading=10
        )

        story = []

        title = context.get(
            "title",
            "Reporte del sistema"
        )

        description = context.get(
            "description"
        )

        report_type = context.get(
            "report_type",
            "general"
        )

        data = context.get(
            "data",
            {}
        )

        records = context.get(
            "records",
            []
        )

        metrics = context.get(
            "metrics",
            {}
        )

        metadata = context.get(
            "metadata",
            {}
        )

        story.append(
            Paragraph(
                str(title),
                title_style
            )
        )

        story.append(
            Spacer(
                1,
                0.4 * cm
            )
        )

        story.append(
            Paragraph(
                f"Tipo de reporte: {report_type}",
                normal_style
            )
        )

        story.append(
            Paragraph(
                (
                    "Generado: "
                    f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                ),
                normal_style
            )
        )

        story.append(
            Spacer(
                1,
                0.5 * cm
            )
        )

        if description:

            story.append(
                Paragraph(
                    str(description),
                    normal_style
                )
            )

            story.append(
                Spacer(
                    1,
                    0.5 * cm
                )
            )

        if data:

            story.append(
                Paragraph(
                    "Información general",
                    heading_style
                )
            )

            table_data = [
                [
                    "Campo",
                    "Valor"
                ]
            ]

            for key, value in data.items():

                table_data.append(
                    [
                        str(key),
                        self._stringify(
                            value
                        )
                    ]
                )

            table = Table(
                table_data,
                repeatRows=1,
                colWidths=[
                    5 * cm,
                    10 * cm
                ]
            )

            table.setStyle(
                self._table_style()
            )

            story.append(
                table
            )

            story.append(
                Spacer(
                    1,
                    0.7 * cm
                )
            )

        if metrics:

            story.append(
                Paragraph(
                    "Métricas",
                    heading_style
                )
            )

            metrics_data = [
                [
                    "Métrica",
                    "Valor"
                ]
            ]

            for key, value in metrics.items():

                metrics_data.append(
                    [
                        str(key),
                        self._stringify(
                            value
                        )
                    ]
                )

            table = Table(
                metrics_data,
                repeatRows=1,
                colWidths=[
                    7 * cm,
                    8 * cm
                ]
            )

            table.setStyle(
                self._table_style()
            )

            story.append(
                table
            )

            story.append(
                Spacer(
                    1,
                    0.7 * cm
                )
            )

        if records:

            story.append(
                Paragraph(
                    "Registros",
                    heading_style
                )
            )

            columns = list(
                records[0].keys()
            )

            table_data = [
                [
                    Paragraph(
                        escape(str(column)),
                        small_style
                    )
                    for column in columns
                ]
            ]

            max_rows = 100

            for record in records[
                :max_rows
            ]:

                row = []

                for column in columns:

                    value = record.get(
                        column
                    )

                    row.append(
                        Paragraph(
                            escape(
                                self._stringify(
                                    value
                                )
                            ),
                            small_style
                        )
                    )

                table_data.append(
                    row
                )

            available_width = (
                A4[0]
                - 4 * cm
            )

            column_width = (
                available_width
                / max(
                    len(columns),
                    1
                )
            )

            table = Table(
                table_data,
                repeatRows=1,
                colWidths=[
                    column_width
                    for _ in columns
                ]
            )

            table.setStyle(
                self._table_style(
                    small=True
                )
            )

            story.append(
                table
            )

            if len(records) > max_rows:

                story.append(
                    Spacer(
                        1,
                        0.3 * cm
                    )
                )

                story.append(
                    Paragraph(
                        (
                            "El reporte muestra los primeros "
                            f"{max_rows} registros de "
                            f"{len(records)}."
                        ),
                        normal_style
                    )
                )

            story.append(
                Spacer(
                    1,
                    0.7 * cm
                )
            )

        if metadata:

            story.append(
                Paragraph(
                    "Metadatos",
                    heading_style
                )
            )

            metadata_data = [
                [
                    "Campo",
                    "Valor"
                ]
            ]

            for key, value in metadata.items():

                metadata_data.append(
                    [
                        str(key),
                        self._stringify(
                            value
                        )
                    ]
                )

            table = Table(
                metadata_data,
                repeatRows=1,
                colWidths=[
                    5 * cm,
                    10 * cm
                ]
            )

            table.setStyle(
                self._table_style()
            )

            story.append(
                table
            )

        document.build(
            story
        )

    def _generate_html(
        self,
        context: dict[str, Any],
        path: Path
    ) -> None:

        title = escape(
            str(
                context.get(
                    "title",
                    "Reporte del sistema"
                )
            )
        )

        description = context.get(
            "description"
        )

        report_type = escape(
            str(
                context.get(
                    "report_type",
                    "general"
                )
            )
        )

        data = context.get(
            "data",
            {}
        )

        records = context.get(
            "records",
            []
        )

        metrics = context.get(
            "metrics",
            {}
        )

        metadata = context.get(
            "metadata",
            {}
        )

        html_parts = [
            "<!DOCTYPE html>",
            "<html lang='es'>",
            "<head>",
            "<meta charset='UTF-8'>",
            f"<title>{title}</title>",
            """
            <style>
                body {
                    font-family: Arial, sans-serif;
                    margin: 40px;
                }

                table {
                    border-collapse: collapse;
                    width: 100%;
                    margin-bottom: 24px;
                }

                th,
                td {
                    border: 1px solid #ddd;
                    padding: 8px;
                    text-align: left;
                }

                th {
                    font-weight: bold;
                }

                h1,
                h2 {
                    margin-top: 24px;
                }
            </style>
            """,
            "</head>",
            "<body>",
            f"<h1>{title}</h1>",
            f"<p><strong>Tipo:</strong> {report_type}</p>",
            (
                "<p><strong>Generado:</strong> "
                f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                "</p>"
            )
        ]

        if description:

            html_parts.append(
                f"<p>{escape(str(description))}</p>"
            )

        if data:

            html_parts.append(
                "<h2>Información general</h2>"
            )

            html_parts.append(
                self._dictionary_to_html_table(
                    data
                )
            )

        if metrics:

            html_parts.append(
                "<h2>Métricas</h2>"
            )

            html_parts.append(
                self._dictionary_to_html_table(
                    metrics
                )
            )

        if records:

            html_parts.append(
                "<h2>Registros</h2>"
            )

            html_parts.append(
                self._records_to_html_table(
                    records
                )
            )

        if metadata:

            html_parts.append(
                "<h2>Metadatos</h2>"
            )

            html_parts.append(
                self._dictionary_to_html_table(
                    metadata
                )
            )

        html_parts.extend(
            [
                "</body>",
                "</html>"
            ]
        )

        path.write_text(
            "\n".join(
                html_parts
            ),
            encoding="utf-8"
        )

    def _generate_json(
        self,
        context: dict[str, Any],
        path: Path
    ) -> None:

        output = {
            "generated_at": (
                datetime.now()
                .isoformat()
            ),
            **context
        }

        path.write_text(
            json.dumps(
                output,
                ensure_ascii=False,
                indent=2,
                default=str
            ),
            encoding="utf-8"
        )

    @staticmethod
    def _dictionary_to_html_table(
        values: dict[str, Any]
    ) -> str:

        rows = [
            "<table>",
            "<thead>",
            "<tr>",
            "<th>Campo</th>",
            "<th>Valor</th>",
            "</tr>",
            "</thead>",
            "<tbody>"
        ]

        for key, value in values.items():

            rows.append(
                (
                    "<tr>"
                    f"<td>{escape(str(key))}</td>"
                    f"<td>{escape(ReportService._stringify(value))}</td>"
                    "</tr>"
                )
            )

        rows.extend(
            [
                "</tbody>",
                "</table>"
            ]
        )

        return "\n".join(
            rows
        )

    @staticmethod
    def _records_to_html_table(
        records: list[dict[str, Any]]
    ) -> str:

        if not records:
            return (
                "<p>No existen registros.</p>"
            )

        columns = list(
            records[0].keys()
        )

        rows = [
            "<table>",
            "<thead>",
            "<tr>"
        ]

        for column in columns:

            rows.append(
                f"<th>{escape(str(column))}</th>"
            )

        rows.extend(
            [
                "</tr>",
                "</thead>",
                "<tbody>"
            ]
        )

        for record in records:

            rows.append(
                "<tr>"
            )

            for column in columns:

                rows.append(
                    (
                        "<td>"
                        f"{escape(ReportService._stringify(record.get(column)))}"
                        "</td>"
                    )
                )

            rows.append(
                "</tr>"
            )

        rows.extend(
            [
                "</tbody>",
                "</table>"
            ]
        )

        return "\n".join(
            rows
        )

    @staticmethod
    def _stringify(
        value: Any
    ) -> str:

        if value is None:
            return ""

        if isinstance(
            value,
            (
                dict,
                list,
                tuple,
                set
            )
        ):
            return json.dumps(
                value,
                ensure_ascii=False,
                default=str
            )

        return str(
            value
        )

    @staticmethod
    def _table_style(
        small: bool = False
    ) -> TableStyle:

        font_size = (
            7
            if small
            else 9
        )

        return TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.lightgrey
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.black
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold"
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    font_size
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP"
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                )
            ]
        )