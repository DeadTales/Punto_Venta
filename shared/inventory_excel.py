"""Contrato Excel único para la vista previa de escritorio y la API."""
from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation
from io import BytesIO
from zipfile import ZipFile

from openpyxl import Workbook, load_workbook
from openpyxl.comments import Comment
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

MAX_BYTES = 5 * 1024 * 1024
MAX_ROWS = 5000
HEADERS = (
    "codigo_barras", "nombre", "categoria", "descripcion", "precio_compra",
    "precio_venta", "stock_actual", "stock_minimo",
)
HELP = (
    "Texto opcional, máximo 50 caracteres. Conserva los ceros iniciales. No repitas códigos.",
    "Obligatorio, máximo 150 caracteres. Nombre que verá el cajero.",
    "Obligatorio, máximo 100 caracteres. Debe existir en el catálogo de categorías.",
    "Descripción opcional del producto.",
    "Costo unitario, de 0 a 99999999.99, máximo 2 decimales.",
    "Precio al público, de 0 a 99999999.99, máximo 2 decimales.",
    "Existencia inicial, de 0 a 9999999.999, máximo 3 decimales. No es un movimiento de entrada.",
    "Alerta de reposición, de 0 a 9999999.999, máximo 3 decimales.",
)


@dataclass(frozen=True)
class InventoryRow:
    fila: int
    codigo_barras: str | None
    nombre: str
    categoria: str
    descripcion: str | None
    precio_compra: Decimal
    precio_venta: Decimal
    stock_actual: Decimal
    stock_minimo: Decimal

    def json(self):
        return {k: str(v) if isinstance(v, Decimal) else v for k, v in asdict(self).items()}


@dataclass
class Preview:
    rows: list[InventoryRow]
    errors: list[dict]

    def json(self):
        return {
            "valid": not self.errors, "count": len(self.rows),
            "rows": [row.json() for row in self.rows], "errors": self.errors,
        }


def template_bytes() -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Inventario"
    ws.append(HEADERS)
    ws.freeze_panes = "C2"
    ws.auto_filter.ref = "A1:H1"
    for index, (header, help_text) in enumerate(zip(HEADERS, HELP), 1):
        cell = ws.cell(1, index)
        cell.font = Font(color="FFFFFF", bold=True)
        cell.fill = PatternFill("solid", fgColor="176B5B")
        cell.comment = Comment(help_text, "POS · Ayuda")
        ws.column_dimensions[cell.column_letter].width = 28 if index < 5 else 21
    # Celdas de texto preformateadas para que Excel no quite ceros del código.
    for row in ws.iter_rows(min_row=2, max_row=101):
        for cell in row:
            cell.number_format = "@" if cell.column <= 4 else "0.00" if cell.column <= 6 else "0.000"
    for column, maximum in (("E", "99999999.99"), ("F", "99999999.99"),
                            ("G", "9999999.999"), ("H", "9999999.999")):
        validation = DataValidation(type="decimal", operator="between", formula1=0, formula2=maximum)
        validation.errorTitle = "Sólo valores positivos o cero"
        validation.error = "Escribe un número dentro del rango indicado en la ayuda."
        validation.showErrorMessage = True
        ws.add_data_validation(validation)
        validation.add(f"{column}2:{column}{MAX_ROWS + 1}")
    guide = wb.create_sheet("Instrucciones")
    instructions = [
        ("PASO", "CÓMO LLENAR LA PLANTILLA"),
        ("1", "Captura tus productos en la hoja Inventario, desde la fila 2. No cambies los encabezados."),
        ("2", "Consulta las categorías del sistema y copia su nombre exacto (ej. General)."),
        ("3", "Los códigos son texto: 001234 conserva sus ceros. Un código por producto; puede quedar vacío."),
        ("4", "Precios: máximo 2 decimales. Existencias: máximo 3. No uses $, separadores de miles ni fórmulas."),
        ("5", "Cada fila crea un producto NUEVO. Un código ya registrado provoca error, nunca reemplaza stock."),
        ("6", "Guarda como .xlsx, máximo 5 MB y 5,000 productos. La hoja Ejemplo no se importa."),
        ("7", "Selecciona el archivo, revisa la vista previa y corrige los errores antes de confirmar."),
        ("8", "Si una fila falla, no se guarda ninguna. Para ajustar productos existentes usa un movimiento de inventario."),
    ]
    for row in instructions:
        guide.append(row)
    guide.column_dimensions["A"].width = 12
    guide.column_dimensions["B"].width = 110
    for row in guide:
        guide.row_dimensions[row[0].row].height = 34
        row[1].alignment = Alignment(wrap_text=True, vertical="center")
    example = wb.create_sheet("Ejemplo (no se importa)")
    example.append(HEADERS)
    example.append(["001234567890", "Agua natural 600 ml", "General", "Botella individual", 6.50, 12, 24, 6])
    output = BytesIO()
    wb.save(output)
    return output.getvalue()


def parse_inventory(data: bytes) -> Preview:
    def failure(message):
        return Preview([], [{"fila": 0, "columna": "archivo", "mensaje": message}])

    if not data or len(data) > MAX_BYTES:
        return failure("El archivo está vacío o supera 5 MB.")
    try:
        with ZipFile(BytesIO(data)) as archive:
            if sum(info.file_size for info in archive.infolist()) > 30 * 1024 * 1024:
                return failure("El contenido descomprimido supera 30 MB.")
        wb = load_workbook(BytesIO(data), read_only=True, data_only=False, keep_links=False)
    except Exception as exc:
        # Los parsers XML también pueden lanzar excepciones específicas del formato.
        return failure(f"No es un archivo Excel .xlsx válido ({type(exc).__name__}).")
    try:
        if "Inventario" not in wb.sheetnames:
            return failure("Falta la hoja Inventario. Descarga y usa la plantilla del sistema.")
        ws = wb["Inventario"]
        if ws.max_row is not None and ws.max_row > MAX_ROWS + 1:
            return failure("La hoja supera 5,000 filas. Divide la importación en varios archivos.")
        if ws.max_column is not None and ws.max_column > len(HEADERS):
            return failure("Hay columnas adicionales. Usa únicamente las ocho columnas de la plantilla.")
        stream = ws.iter_rows(max_col=len(HEADERS), max_row=MAX_ROWS + 2)
        first = next(stream)
        if tuple(c.value for c in first) != HEADERS:
            return failure("Los encabezados no coinciden con la plantilla. No cambies su orden ni sus nombres.")
        rows, errors, codes = [], [], set()
        for number, cells in enumerate(stream, 2):
            values = [c.value for c in cells]
            if all(v is None or isinstance(v, str) and not v.strip() for v in values):
                continue
            if number > MAX_ROWS + 1:
                return failure("El archivo supera 5,000 productos.")
            cleaned = {}
            before = len(errors)
            for column, (header, value) in enumerate(zip(HEADERS, values)):
                def error(message):
                    errors.append({"fila": number, "columna": header, "mensaje": message})
                if cells[column].data_type in {"f", "e"}:
                    error("No se permiten fórmulas ni errores de Excel; escribe el valor directamente.")
                    continue
                if column < 4:
                    if value is not None and not isinstance(value, str):
                        error("Usa formato Texto; los códigos numéricos pueden perder ceros iniciales.")
                        continue
                    text = (value or "").strip()
                    if column in (1, 2) and not text:
                        error("Este campo es obligatorio.")
                    if column < 3 and len(text) > (50, 150, 100)[column]:
                        error("El texto excede la longitud permitida.")
                    cleaned[header] = text or None
                else:
                    precision = 2 if column in (4, 5) else 3
                    maximum = Decimal("99999999.99" if precision == 2 else "9999999.999")
                    try:
                        amount = Decimal(str(value))
                        if not amount.is_finite() or not 0 <= amount <= maximum:
                            raise ValueError
                        if amount != amount.quantize(Decimal(1).scaleb(-precision)):
                            raise ValueError
                        cleaned[header] = amount
                    except (InvalidOperation, ValueError):
                        error(f"Escribe un número entre 0 y {maximum}, máximo {precision} decimales.")
            code = cleaned.get("codigo_barras")
            if code and code in codes:
                errors.append({"fila": number, "columna": "codigo_barras", "mensaje": "Código repetido dentro del archivo."})
            if code:
                codes.add(code)
            if len(errors) == before:
                rows.append(InventoryRow(fila=number, **cleaned))
        if not rows and not errors:
            return failure("No hay productos. Llena la hoja Inventario desde la fila 2; Ejemplo no se importa.")
        return Preview(rows, errors)
    finally:
        wb.close()
