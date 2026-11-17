"""Tickets de texto y PDF a partir de un detalle de venta ya confirmado."""

import textwrap
from decimal import Decimal
from io import BytesIO


def _clean(value):
    printable = "".join(
        character
        for character in str(value or "")
        if character.isprintable() or character.isspace()
    )

    return " ".join(printable.split())


def receipt_lines(sale, business_name="Punto · Sistema POS", width=36):
    lines = [
        _clean(business_name),
        f"Ticket #{sale['id_venta']}",
        _clean(sale.get("fecha_hora")),
        "Empleado: " + _clean(sale.get("empleado", "—")),
        "Cliente: " + _clean(sale.get("cliente") or "Público general"),
        "-" * width,
    ]

    for item in sale.get("items", []):
        lines.extend(textwrap.wrap(_clean(item["nombre"]), width) or [""])
        lines.append(
            f"{item['cantidad']} x ${Decimal(str(item['precio_unitario_venta'])):.2f}  ${Decimal(str(item['subtotal'])):.2f}"
        )

    total = Decimal(str(sale["total"]))
    tax = Decimal(str(sale.get("impuesto", 0)))
    lines.extend(
        [
            "-" * width,
            f"Subtotal: ${total - tax:.2f}",
            f"Impuesto incluido: ${tax:.2f}",
            f"TOTAL: ${total:.2f}",
            "Pago: " + _clean(sale.get("metodo_pago", "—")),
        ]
    )

    if sale.get("estado") == "Cancelada":
        lines.extend(["VENTA CANCELADA", _clean(sale.get("cancel_motivo"))])

    lines.extend(
        ["Gracias por tu compra", "Comprobante de venta; no es factura fiscal."]
    )

    return [
        part
        for line in lines
        for part in (textwrap.wrap(line, width, replace_whitespace=True) or [""])
    ]


def receipt_pdf(sale, business_name="Punto · Sistema POS"):
    from reportlab.pdfgen import canvas

    output = BytesIO()
    pdf = canvas.Canvas(output, pagesize=(227, 842))
    pdf.setTitle(f"Ticket {sale['id_venta']}")
    pdf.setAuthor(business_name)
    position = 820
    pdf.setFont("Helvetica", 9)

    for line in receipt_lines(sale, business_name):
        if position < 25:
            pdf.showPage()
            pdf.setFont("Helvetica", 9)
            position = 820

        pdf.drawString(12, position, line)
        position -= 13

    pdf.save()

    return output.getvalue()
