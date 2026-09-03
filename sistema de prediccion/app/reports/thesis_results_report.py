from __future__ import annotations

import json

from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    ParagraphStyle,
    getSampleStyleSheet,
)
from reportlab.lib.units import cm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


class ThesisResultsReport:

    # ==========================================
    # GENERAR
    # ==========================================

    def generate(
        self,
        context: dict[str, Any],
        report_format: str,
        filename: str,
        base_dir: Path
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
                "El nombre del reporte "
                "es obligatorio"
            )

        base_dir = Path(
            base_dir
        )

        base_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        if report_format == "pdf":

            path = (
                base_dir
                /
                f"{filename}.pdf"
            )

            self._generate_pdf(
                context=context,
                path=path
            )

        elif report_format == "html":

            path = (
                base_dir
                /
                f"{filename}.html"
            )

            self._generate_html(
                context=context,
                path=path
            )

        elif report_format == "json":

            path = (
                base_dir
                /
                f"{filename}.json"
            )

            self._generate_json(
                context=context,
                path=path
            )

        else:

            raise ValueError(
                "Formato no soportado: "
                f"{report_format}"
            )

        if not path.exists():

            raise RuntimeError(
                "No se pudo generar "
                "el reporte de tesis"
            )

        return path

    # ==========================================
    # PDF
    # ==========================================

    def _generate_pdf(
        self,
        context: dict[str, Any],
        path: Path
    ) -> None:

        document = SimpleDocTemplate(
            str(path),
            pagesize=A4,
            rightMargin=1.5 * cm,
            leftMargin=1.5 * cm,
            topMargin=1.5 * cm,
            bottomMargin=1.5 * cm
        )

        styles = (
            getSampleStyleSheet()
        )

        title_style = (
            styles["Title"]
        )

        heading_style = (
            styles["Heading2"]
        )

        normal_style = (
            styles["BodyText"]
        )

        small_style = ParagraphStyle(
            "ThesisSmall",
            parent=normal_style,
            fontSize=7,
            leading=9
        )

        note_style = ParagraphStyle(
            "ThesisNote",
            parent=normal_style,
            fontSize=8,
            leading=11,
            leftIndent=0.3 * cm,
            rightIndent=0.3 * cm,
            spaceBefore=4,
            spaceAfter=8
        )

        story = []

        # ======================================
        # PORTADA
        # ======================================

        title = context.get(
            "title",
            (
                "Reporte consolidado "
                "de resultados"
            )
        )

        story.append(
            Paragraph(
                escape(
                    str(title)
                ),
                title_style
            )
        )

        story.append(
            Spacer(
                1,
                0.4 * cm
            )
        )

        subtitle = context.get(
            "subtitle"
        )

        if subtitle:

            story.append(
                Paragraph(
                    escape(
                        str(subtitle)
                    ),
                    heading_style
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
                (
                    "<b>Fecha de generación:</b> "
                    f"{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
                ),
                normal_style
            )
        )

        description = context.get(
            "description"
        )

        if description:

            story.append(
                Spacer(
                    1,
                    0.3 * cm
                )
            )

            story.append(
                Paragraph(
                    escape(
                        str(description)
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

        methodological_note = (
            context.get(
                "methodological_note"
            )
        )

        if methodological_note:

            story.append(
                Paragraph(
                    (
                        "<b>Nota metodológica:</b> "
                        f"{escape(str(methodological_note))}"
                    ),
                    note_style
                )
            )

        story.append(
            PageBreak()
        )

        # ======================================
        # SECCIONES
        # ======================================

        sections = (
            context.get(
                "sections",
                []
            )
        )

        for section in sections:

            title = section.get(
                "title",
                "Sección"
            )

            story.append(
                Paragraph(
                    escape(
                        str(title)
                    ),
                    heading_style
                )
            )

            story.append(
                Spacer(
                    1,
                    0.2 * cm
                )
            )

            text = section.get(
                "text"
            )

            if text:

                story.append(
                    Paragraph(
                        escape(
                            str(text)
                        ),
                        normal_style
                    )
                )

                story.append(
                    Spacer(
                        1,
                        0.3 * cm
                    )
                )

            section_type = (
                section.get(
                    "type",
                    "key_value"
                )
            )

            if section_type == "key_value":

                data = section.get(
                    "data",
                    {}
                )

                if data:

                    table = (
                        self._build_key_value_table(
                            data=data,
                            small_style=(
                                small_style
                            )
                        )
                    )

                    story.append(
                        table
                    )

            elif section_type == "table":

                records = section.get(
                    "records",
                    []
                )

                if records:

                    table = (
                        self._build_records_table(
                            records=records,
                            small_style=(
                                small_style
                            )
                        )
                    )

                    story.append(
                        table
                    )

                else:

                    story.append(
                        Paragraph(
                            (
                                "No existen datos "
                                "disponibles para "
                                "esta sección."
                            ),
                            normal_style
                        )
                    )

            elif section_type == "text":

                if not text:

                    story.append(
                        Paragraph(
                            (
                                "No existen datos "
                                "disponibles."
                            ),
                            normal_style
                        )
                    )

            story.append(
                Spacer(
                    1,
                    0.6 * cm
                )
            )

        document.build(
            story
        )

    # ==========================================
    # TABLA KEY VALUE
    # ==========================================

    def _build_key_value_table(
        self,
        data: dict[str, Any],
        small_style
    ) -> Table:

        rows = [
            [
                Paragraph(
                    "<b>Campo</b>",
                    small_style
                ),
                Paragraph(
                    "<b>Valor</b>",
                    small_style
                ),
            ]
        ]

        for key, value in data.items():

            rows.append(
                [
                    Paragraph(
                        escape(
                            self._label(
                                key
                            )
                        ),
                        small_style
                    ),
                    Paragraph(
                        escape(
                            self._stringify(
                                value
                            )
                        ),
                        small_style
                    ),
                ]
            )

        table = Table(
            rows,
            repeatRows=1,
            colWidths=[
                6 * cm,
                10.5 * cm,
            ]
        )

        table.setStyle(
            self._table_style()
        )

        return table

    # ==========================================
    # TABLA DE REGISTROS
    # ==========================================

    def _build_records_table(
        self,
        records: list[dict],
        small_style
    ) -> Table:

        columns = list(
            records[0].keys()
        )

        rows = [
            [
                Paragraph(
                    (
                        "<b>"
                        f"{escape(self._label(column))}"
                        "</b>"
                    ),
                    small_style
                )
                for column
                in columns
            ]
        ]

        max_rows = 100

        for record in (
            records[:max_rows]
        ):

            rows.append(
                [
                    Paragraph(
                        escape(
                            self._stringify(
                                record.get(
                                    column
                                )
                            )
                        ),
                        small_style
                    )
                    for column
                    in columns
                ]
            )

        available_width = (
            A4[0]
            -
            3 * cm
        )

        column_width = (
            available_width
            /
            max(
                len(columns),
                1
            )
        )

        table = Table(
            rows,
            repeatRows=1,
            colWidths=[
                column_width
                for _ in columns
            ]
        )

        table.setStyle(
            self._table_style()
        )

        return table

    # ==========================================
    # HTML
    # ==========================================

    def _generate_html(
        self,
        context: dict[str, Any],
        path: Path
    ) -> None:

        title = escape(
            str(
                context.get(
                    "title",
                    "Reporte de resultados"
                )
            )
        )

        parts = [
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
                    line-height: 1.5;
                }

                table {
                    border-collapse: collapse;
                    width: 100%;
                    margin-bottom: 25px;
                }

                th,
                td {
                    border: 1px solid #cccccc;
                    padding: 7px;
                    text-align: left;
                    vertical-align: top;
                }

                th {
                    font-weight: bold;
                }

                h1 {
                    margin-bottom: 10px;
                }

                h2 {
                    margin-top: 30px;
                }

                .note {
                    padding: 12px;
                    border: 1px solid #cccccc;
                    margin: 20px 0;
                }
            </style>
            """,
            "</head>",
            "<body>",
            f"<h1>{title}</h1>",
        ]

        subtitle = context.get(
            "subtitle"
        )

        if subtitle:

            parts.append(
                f"<h3>{escape(str(subtitle))}</h3>"
            )

        parts.append(
            (
                "<p><strong>Fecha de generación:</strong> "
                f"{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
                "</p>"
            )
        )

        description = context.get(
            "description"
        )

        if description:

            parts.append(
                f"<p>{escape(str(description))}</p>"
            )

        methodological_note = (
            context.get(
                "methodological_note"
            )
        )

        if methodological_note:

            parts.append(
                (
                    "<div class='note'>"
                    "<strong>Nota metodológica:</strong> "
                    f"{escape(str(methodological_note))}"
                    "</div>"
                )
            )

        for section in (
            context.get(
                "sections",
                []
            )
        ):

            parts.append(
                f"<h2>{escape(str(section.get('title', 'Sección')))}</h2>"
            )

            text = (
                section.get(
                    "text"
                )
            )

            if text:

                parts.append(
                    f"<p>{escape(str(text))}</p>"
                )

            section_type = (
                section.get(
                    "type",
                    "key_value"
                )
            )

            if section_type == "key_value":

                parts.append(
                    self._dictionary_to_html_table(
                        section.get(
                            "data",
                            {}
                        )
                    )
                )

            elif section_type == "table":

                parts.append(
                    self._records_to_html_table(
                        section.get(
                            "records",
                            []
                        )
                    )
                )

        parts.extend(
            [
                "</body>",
                "</html>",
            ]
        )

        path.write_text(
            "\n".join(
                parts
            ),
            encoding="utf-8"
        )

    # ==========================================
    # JSON
    # ==========================================

    @staticmethod
    def _generate_json(
        context: dict[str, Any],
        path: Path
    ) -> None:

        output = {
            "generated_at": (
                datetime.now()
                .isoformat()
            ),
            **context,
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

    # ==========================================
    # HTML KEY VALUE
    # ==========================================

    @classmethod
    def _dictionary_to_html_table(
        cls,
        data: dict
    ) -> str:

        if not data:

            return (
                "<p>No existen datos "
                "disponibles.</p>"
            )

        rows = [
            "<table>",
            "<thead>",
            "<tr>",
            "<th>Campo</th>",
            "<th>Valor</th>",
            "</tr>",
            "</thead>",
            "<tbody>",
        ]

        for key, value in data.items():

            rows.append(
                (
                    "<tr>"
                    f"<td>{escape(cls._label(key))}</td>"
                    f"<td>{escape(cls._stringify(value))}</td>"
                    "</tr>"
                )
            )

        rows.extend(
            [
                "</tbody>",
                "</table>",
            ]
        )

        return "\n".join(
            rows
        )

    # ==========================================
    # HTML RECORDS
    # ==========================================

    @classmethod
    def _records_to_html_table(
        cls,
        records: list[dict]
    ) -> str:

        if not records:

            return (
                "<p>No existen registros "
                "disponibles.</p>"
            )

        columns = list(
            records[0].keys()
        )

        rows = [
            "<table>",
            "<thead>",
            "<tr>",
        ]

        for column in columns:

            rows.append(
                f"<th>{escape(cls._label(column))}</th>"
            )

        rows.extend(
            [
                "</tr>",
                "</thead>",
                "<tbody>",
            ]
        )

        for record in records[:100]:

            rows.append(
                "<tr>"
            )

            for column in columns:

                rows.append(
                    (
                        "<td>"
                        f"{escape(cls._stringify(record.get(column)))}"
                        "</td>"
                    )
                )

            rows.append(
                "</tr>"
            )

        rows.extend(
            [
                "</tbody>",
                "</table>",
            ]
        )

        return "\n".join(
            rows
        )

    # ==========================================
    # LABEL
    # ==========================================

    @staticmethod
    def _label(
        value: Any
    ) -> str:

        return (
            str(value)
            .replace(
                "_",
                " "
            )
            .strip()
            .capitalize()
        )

    # ==========================================
    # STRINGIFY
    # ==========================================

    @staticmethod
    def _stringify(
        value: Any
    ) -> str:

        if value is None:

            return "No disponible"

        if isinstance(
            value,
            float
        ):

            return (
                f"{value:.4f}"
            )

        if isinstance(
            value,
            (
                dict,
                list,
                tuple,
                set,
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

    # ==========================================
    # TABLE STYLE
    # ==========================================

    @staticmethod
    def _table_style() -> TableStyle:

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
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold"
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey
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
                    4
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    4
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    4
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    4
                ),
            ]
        )