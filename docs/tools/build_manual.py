"""Genera las figuras SVG, actualiza Markdown y exporta el manual ilustrado a PDF."""

import base64
import math
import re
from pathlib import Path
from xml.sax.saxutils import escape

from manual_figures import FIGURES
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Flowable,
    KeepTogether,
    LongTable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
SOURCE = DOCS / "manual_usuario.md"
TARGET = SOURCE.with_suffix(".pdf")
ANNOTATED = DOCS / "manual/anotadas"
GREEN = colors.HexColor("#176B5B")
ORANGE = colors.HexColor("#C44416")
SCREEN_WIDTH = 1440
SCREEN_HEIGHT = 1080
RADIUS = 18


def register_fonts():
    directory = Path("C:/Windows/Fonts")

    for name, filename in (
        ("Manual", "arial.ttf"),
        ("Manual-Bold", "arialbd.ttf"),
        ("Manual-Italic", "ariali.ttf"),
        ("Manual-BoldItalic", "arialbi.ttf"),
    ):
        pdfmetrics.registerFont(TTFont(name, str(directory / filename)))

    pdfmetrics.registerFontFamily(
        "Manual",
        normal="Manual",
        bold="Manual-Bold",
        italic="Manual-Italic",
        boldItalic="Manual-BoldItalic",
    )


def make_styles():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            "ManualBody",
            fontName="Manual",
            fontSize=10,
            leading=14.5,
            spaceAfter=8,
            textColor=colors.HexColor("#26332F"),
            alignment=TA_LEFT,
        )
    )

    for level, size in ((1, 25), (2, 15), (3, 11.5)):
        styles.add(
            ParagraphStyle(
                f"ManualHeading{level}",
                parent=styles["ManualBody"],
                fontName="Manual-Bold",
                fontSize=size,
                leading=size * 1.25,
                textColor=GREEN,
                spaceBefore=16 if level != 1 else 0,
                spaceAfter=9,
                keepWithNext=True,
            )
        )

    styles.add(
        ParagraphStyle(
            "ManualCell",
            parent=styles["ManualBody"],
            fontSize=8.5,
            leading=11.5,
            spaceAfter=0,
        )
    )
    styles.add(
        ParagraphStyle(
            "ManualCellHeader",
            parent=styles["ManualCell"],
            fontName="Manual-Bold",
            textColor=colors.white,
        )
    )
    styles.add(
        ParagraphStyle(
            "ManualCaption",
            parent=styles["ManualBody"],
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#5C6A64"),
        )
    )

    return styles


def inline(value):
    value = escape(value)
    value = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1", value)
    value = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", value)
    value = re.sub(r"`([^`]+)`", r'<font color="#176B5B">\1</font>', value)

    return value


def image_path(figure):
    return DOCS / "manual/capturas" / f"{figure.scene}.png"


def crop_bounds(figure):
    x, y, width, height = figure.crop
    left, top, right, bottom = x, y, x + width, y + height

    for marker in figure.markers:
        mx, my = marker.position
        left = min(left, mx - RADIUS - 4)
        top = min(top, my - RADIUS - 4)
        right = max(right, mx + RADIUS + 4)
        bottom = max(bottom, my + RADIUS + 4)

    left, top = max(0, left), max(0, top)
    right, bottom = min(SCREEN_WIDTH, right), min(SCREEN_HEIGHT, bottom)

    return left, top, right - left, bottom - top


def validate_figure(figure):
    image = ImageReader(str(image_path(figure)))

    if image.getSize() != (SCREEN_WIDTH, SCREEN_HEIGHT):
        raise ValueError(f"Dimensiones inesperadas: {figure.scene}")

    left, top, width, height = crop_bounds(figure)

    for marker in figure.markers:
        for x, y in (marker.target, marker.position):
            if not left <= x <= left + width or not top <= y <= top + height:
                raise ValueError(f"Referencia fuera del recorte: {figure.scene}")


def write_svg(figure):
    left, top, width, height = crop_bounds(figure)
    screenshot = base64.b64encode(image_path(figure).read_bytes()).decode("ascii")
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="{left} {top} {width} {height}" role="img" aria-labelledby="title description">',
        f'<title id="title">{escape(figure.title)}</title>',
        '<desc id="description">Captura real con datos ficticios. '
        + escape(
            " ".join(
                f"{index}. {marker.text}"
                for index, marker in enumerate(figure.markers, 1)
            )
        )
        + "</desc>",
        '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" '
        'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
        '<path d="M 0 0 L 10 5 L 0 10 z" fill="#C44416"/></marker></defs>',
        f'<image width="{SCREEN_WIDTH}" height="{SCREEN_HEIGHT}" href="data:image/png;base64,{screenshot}"/>',
    ]

    for index, marker in enumerate(figure.markers, 1):
        x, y = marker.position
        target_x, target_y = marker.target
        parts.extend(
            [
                f'<line x1="{x}" y1="{y}" x2="{target_x}" y2="{target_y}" '
                'stroke="#C44416" stroke-width="3" marker-end="url(#arrow)"/>',
                f'<circle cx="{x}" cy="{y}" r="{RADIUS}" fill="#C44416" stroke="white" stroke-width="3"/>',
                f'<text x="{x}" y="{y + 7}" text-anchor="middle" '
                f'font-family="Arial,sans-serif" font-weight="bold" font-size="21" fill="white">{index}</text>',
            ]
        )

    parts.append("</svg>")
    (ANNOTATED / f"{figure.scene}.svg").write_text("\n".join(parts), encoding="utf-8")


def figure_markdown(figure, number):
    title = f"Figura {number:02d}. {figure.title}"
    rows = [
        f"<!-- manual-figure:{figure.scene}:start -->",
        f"### {title}",
        "",
        f"![{title}](manual/anotadas/{figure.scene}.svg)",
        "",
        f"[Abrir captura original](manual/capturas/{figure.scene}.png). Datos ficticios; los números corresponden a la tabla siguiente.",
        "",
        "| N.º | Elemento y función |",
        "| --- | --- |",
    ]

    for index, marker in enumerate(figure.markers, 1):
        name, _, detail = marker.text.partition(": ")
        rows.append(f"| {index} | **{name}:** {detail} |")

    rows.extend(["", f"<!-- manual-figure:{figure.scene}:end -->", ""])

    return "\n".join(rows) + "\n"


def update_markdown():
    source = SOURCE.read_text(encoding="utf-8")
    source = re.sub(
        r"<!-- manual-figure:[^:]+:start -->.*?<!-- manual-figure:[^:]+:end -->\n*",
        "",
        source,
        flags=re.S,
    )
    source = source.replace("Versión del manual: 1.0", "Versión del manual: 1.1")

    for number, figure in enumerate(FIGURES, 1):
        anchor = figure.before + "\n"

        if source.count(anchor) != 1:
            raise ValueError(f"Sección de inserción ambigua: {figure.before}")

        source = source.replace(anchor, figure_markdown(figure, number) + anchor, 1)

    SOURCE.write_text(source, encoding="utf-8")


class AnnotatedScreenshot(Flowable):
    """Imagen original y referencias vectoriales; no altera los píxeles capturados."""

    def __init__(self, figure, max_width, max_height):
        super().__init__()
        self.figure = figure
        self.crop = crop_bounds(figure)
        _, _, width, height = self.crop
        self.scale = min(max_width / width, max_height / height)
        self.width = width * self.scale
        self.height = height * self.scale
        self.hAlign = "CENTER"

    def draw(self):
        canvas = self.canv
        left, top, width, height = self.crop
        canvas.saveState()
        canvas.scale(self.scale, self.scale)
        clipping = canvas.beginPath()
        clipping.rect(0, 0, width, height)
        canvas.clipPath(clipping, stroke=0)
        canvas.translate(-left, -(SCREEN_HEIGHT - top - height))
        canvas.drawImage(
            str(image_path(self.figure)),
            0,
            0,
            width=SCREEN_WIDTH,
            height=SCREEN_HEIGHT,
        )

        for number, marker in enumerate(self.figure.markers, 1):
            self.draw_marker(canvas, marker, number)

        canvas.restoreState()

    @staticmethod
    def draw_marker(canvas, marker, number):
        x, screen_y = marker.position
        target_x, target_screen_y = marker.target
        y, target_y = SCREEN_HEIGHT - screen_y, SCREEN_HEIGHT - target_screen_y
        canvas.setStrokeColor(ORANGE)
        canvas.setFillColor(ORANGE)
        canvas.setLineWidth(3)
        canvas.line(x, y, target_x, target_y)
        angle = math.atan2(target_y - y, target_x - x)
        arrow = canvas.beginPath()
        arrow.moveTo(target_x, target_y)

        for offset in (-0.5, 0.5):
            arrow.lineTo(
                target_x - 10 * math.cos(angle + offset),
                target_y - 10 * math.sin(angle + offset),
            )

        arrow.close()
        canvas.drawPath(arrow, fill=1, stroke=0)
        canvas.setStrokeColor(colors.white)
        canvas.circle(x, y, RADIUS, fill=1, stroke=1)
        canvas.setFont("Manual-Bold", 21)
        canvas.setFillColor(colors.white)
        canvas.drawCentredString(x, y - 7, str(number))


def make_table(cells, width, styles, ratios=None):
    header, *rows = cells
    count = len(header)
    ratios = ratios or ([0.49, 0.17, 0.17, 0.17] if count == 4 else [0.28, 0.72])
    data = [[Paragraph(inline(value), styles["ManualCellHeader"]) for value in header]]
    data.extend(
        [Paragraph(inline(value), styles["ManualCell"]) for value in row]
        for row in rows
    )
    table = LongTable(
        data,
        colWidths=[width * ratio for ratio in ratios],
        repeatRows=1,
        hAlign="LEFT",
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), GREEN),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.white, colors.HexColor("#F0F6F3")],
                ),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LINEBELOW", (0, 0), (-1, -1), 0.3, colors.HexColor("#D7E4DE")),
            ]
        )
    )

    return table


def make_figure(figure, number, width, page_height, styles):
    cells = [["N.º", "Elemento y función"]]

    for index, marker in enumerate(figure.markers, 1):
        name, _, detail = marker.text.partition(": ")
        cells.append([str(index), f"**{name}:** {detail}"])

    legend = make_table(cells, width, styles, ratios=[0.08, 0.92])
    _, legend_height = legend.wrap(width, page_height)
    max_height = min(430, page_height - legend_height - 100)

    if max_height < 150:
        raise ValueError(f"La leyenda ocupa demasiado espacio: {figure.scene}")

    return KeepTogether(
        [
            Paragraph(
                f"Figura {number:02d}. {inline(figure.title)}", styles["ManualHeading3"]
            ),
            AnnotatedScreenshot(figure, width, max_height),
            Spacer(1, 7),
            Paragraph(
                "Captura real del frontend con datos ficticios. Referencias numeradas:",
                styles["ManualCaption"],
            ),
            legend,
            Spacer(1, 12),
        ]
    )


def footer(canvas, document):
    canvas.saveState()
    width, _ = A4
    canvas.setStrokeColor(colors.HexColor("#D7E4DE"))
    canvas.line(42, 39, width - 42, 39)
    canvas.setFont("Manual", 8)
    canvas.setFillColor(colors.HexColor("#5C6A64"))
    canvas.drawString(42, 26, "Punto · Manual ilustrado de usuario · Versión 1.1")
    canvas.drawRightString(width - 42, 26, f"Página {document.page}")
    canvas.restoreState()


class ManualDocument(SimpleDocTemplate):
    def afterFlowable(self, flowable):
        if not isinstance(flowable, Paragraph):
            return

        title = flowable.getPlainText()

        if flowable.style.name == "ManualHeading2":
            key = "section-" + re.sub(r"[^a-z0-9]+", "-", title.casefold())
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(title, key, level=0)
        elif flowable.style.name == "ManualHeading3" and title.startswith("Figura "):
            key = "figure-" + title.split(".", 1)[0].split()[-1]
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(title, key, level=1)


def build_pdf():
    register_fonts()
    styles = make_styles()
    document = ManualDocument(
        str(TARGET),
        pagesize=A4,
        rightMargin=42,
        leftMargin=42,
        topMargin=42,
        bottomMargin=54,
        title="Manual ilustrado de usuario de Punto",
        author="Punto · Sistema de punto de venta",
    )
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    figures = {
        figure.scene: (number, figure) for number, figure in enumerate(FIGURES, 1)
    }
    story = []
    index = 0

    while index < len(lines):
        line = lines[index].strip()
        match = re.fullmatch(r"<!-- manual-figure:([^:]+):start -->", line)

        if match:
            scene = match[1]
            number, figure = figures[scene]
            story.append(
                make_figure(figure, number, document.width, document.height, styles)
            )

            while lines[index].strip() != f"<!-- manual-figure:{scene}:end -->":
                index += 1

            index += 1
            continue

        if not line:
            index += 1
            continue

        if line.startswith("|"):
            cells = []

            while index < len(lines) and lines[index].strip().startswith("|"):
                row = [
                    value.strip()
                    for value in lines[index].strip().strip("|").split("|")
                ]

                if not all(re.fullmatch(r"[-: ]+", value) for value in row):
                    cells.append(row)

                index += 1

            story.extend([make_table(cells, document.width, styles), Spacer(1, 10)])
            continue

        heading = re.match(r"^(#{1,3}) (.+)$", line)

        if heading:
            story.append(
                Paragraph(inline(heading[2]), styles[f"ManualHeading{len(heading[1])}"])
            )
        else:
            line = "• " + line[2:] if line.startswith("- ") else line
            story.append(Paragraph(inline(line), styles["ManualBody"]))

        index += 1

    document.build(story, onFirstPage=footer, onLaterPages=footer)
    print(
        f"PDF ilustrado generado: {TARGET.relative_to(ROOT)} ({TARGET.stat().st_size:,} bytes)"
    )


def main():
    ANNOTATED.mkdir(parents=True, exist_ok=True)

    for figure in FIGURES:
        validate_figure(figure)
        write_svg(figure)

    update_markdown()
    build_pdf()
    print(f"Figuras verificadas e incluidas: {len(FIGURES)}")


if __name__ == "__main__":
    main()
