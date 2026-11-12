import csv
from datetime import datetime, timedelta
from decimal import Decimal
from io import StringIO

import flet as ft

from ..components.ui import GREEN, MUTED, card, heading, note, pill, primary, stat, table, tabs, text
from ..models.state import money
from .pos_view import sales_chart


def reports_view(app):
    state = app.state
    kind = app.route.split("/")[1]
    period = int(app.filters.get("report_days", 7))
    start = datetime.now().date() - timedelta(days=period - 1)
    sales = [s for s in state.sales if s["estado"] == "Completada" and datetime.fromisoformat(s["fecha_hora"]).date() >= start]
    total = sum((Decimal(str(s["total"])) for s in sales), Decimal(0))
    titles = {"ventas": "Ventas", "clientes": "Clientes", "usuarios": "Usuarios", "predicciones": "Predicciones"}
    selector = ft.Dropdown(value=str(period), width=190, dense=True, label="Periodo",
                           options=[ft.DropdownOption("7", "Últimos 7 días"), ft.DropdownOption("30", "Últimos 30 días")])

    def change(e):
        app.filters["report_days"] = e.control.value
        app.render()

    selector.on_select = change
    if kind == "ventas":
        headers = ["TICKET", "FECHA", "MÉTODO", "TOTAL"]
        rows = [[s["id_venta"], s["fecha_hora"].replace("T", " ")[:16], next((m["nombre"] for m in state.methods if m["id_metodo_pago"] == s["id_metodo_pago"]), "—"), money(s["total"])] for s in sorted(sales, key=lambda s: s["fecha_hora"], reverse=True)]
    elif kind in {"clientes", "usuarios"}:
        is_client = kind == "clientes"
        items, key = (state.clients, "id_cliente") if is_client else (state.users, "id_empleado")
        headers = ["CLIENTE" if is_client else "USUARIO", "VENTAS", "IMPORTE", "PROMEDIO"]
        rows = []
        for item in items:
            related = [s for s in sales if s.get(key) == item[key]]
            amount = sum((Decimal(str(s["total"])) for s in related), Decimal(0))
            rows.append([item["nombre"] + (" " + item.get("apellido", "") if not is_client else ""), len(related), money(amount), money(amount / len(related) if related else 0)])
        if is_client:
            general = [s for s in sales if s.get("id_cliente") is None]
            amount = sum((Decimal(str(s["total"])) for s in general), Decimal(0))
            rows.append(["Público general", len(general), money(amount), money(amount / len(general) if general else 0)])
    else:
        average = total / period
        headers = ["INDICADOR", "ESTIMACIÓN", "MÉTODO"]
        rows = [["Venta diaria", money(average) if sales else "Sin datos", f"Media de {period} días (incluye días sin ventas)"],
                ["Próximos 7 días", money(average * 7) if sales else "Sin datos", "Proyección lineal sin estacionalidad"],
                ["Reposición por producto", "Pendiente", "Requiere historial por artículo y plazo de proveedores"]]

    async def export(e):
        output = StringIO(newline="")
        writer = csv.writer(output)
        def safe(value):
            value = str(value)
            return "'" + value if value.startswith(("=", "+", "-", "@")) else value
        writer.writerow(headers)
        writer.writerows([[safe(v) for v in row] for row in rows])
        try:
            await app.picker.save_file(file_name=f"reporte_{kind}.csv", src_bytes=output.getvalue().encode("utf-8-sig"))
        except Exception as exc:
            app.notify(str(exc), error=True)

    return ft.Column([
        heading("Reportes", "Información para decidir con claridad.", [selector, primary("Exportar CSV", export, ft.Icons.DOWNLOAD)]),
        tabs(app, "reportes"),
        ft.ResponsiveRow([
            stat("Ventas del periodo", money(total), f"Últimos {period} días", ft.Icons.TRENDING_UP),
            stat("Operaciones", len(sales), "Ventas completadas", ft.Icons.RECEIPT_LONG_OUTLINED),
            stat("Ticket promedio", money(total / len(sales) if sales else 0), "Promedio por comprobante", ft.Icons.BAR_CHART_OUTLINED),
            stat("Clientes registrados", len(state.clients), "Directorio cargado", ft.Icons.PEOPLE_OUTLINE),
        ], spacing=16, run_spacing=16),
        *([card(ft.Column([text("Tendencia de los últimos 7 días", 17, True), sales_chart(state)], spacing=20))] if kind in {"ventas", "predicciones"} else []),
        card(ft.Column([text(titles[kind], 18, True), table(headers, rows)], spacing=18)),
        note("Predicción exploratoria basada en una media simple. No hay un modelo de aprendizaje automático entrenado; una muestra vacía no permite proyectar demanda." if kind == "predicciones" else
             "Resumen calculado con los registros cargados. En modo API se consultan hasta las 500 ventas más recientes; falta paginación histórica para un reporte contable completo."),
    ], spacing=22)
