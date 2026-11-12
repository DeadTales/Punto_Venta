from datetime import datetime
from decimal import Decimal

import flet as ft

from ..components.ui import GREEN, MUTED, card, heading, note, pill, primary, secondary, stat, table, tabs, text
from ..models.state import money


def today_sales(state):
    today = datetime.now().date().isoformat()
    return [s for s in state.sales if s["fecha_hora"].startswith(today) and s["estado"] == "Completada"]


def cash_view(app):
    state = app.state
    if app.route == "caja/corte":
        return cut_view(app)
    sales = today_sales(state)
    total = sum((Decimal(str(s["total"])) for s in sales), Decimal(0))
    return ft.Column([
        heading("Tu negocio, al día", "Un vistazo a la operación y acceso directo a lo importante.",
                [primary("Nueva venta", lambda e: app.navigate("carrito"), ft.Icons.ADD_SHOPPING_CART)]),
        tabs(app, "caja"),
        ft.ResponsiveRow([
            stat("Ventas de hoy", money(total), "Ventas completadas · MXN", ft.Icons.TRENDING_UP),
            stat("Tickets de hoy", len(sales), "Comprobantes registrados", ft.Icons.RECEIPT_LONG_OUTLINED),
            stat("Ticket promedio", money(total / len(sales) if sales else 0), "Importe medio por operación", ft.Icons.BAR_CHART_OUTLINED),
            stat("Alertas de stock", len(state.low_stock), "Productos que necesitan atención", ft.Icons.INVENTORY_2_OUTLINED),
        ], spacing=16, run_spacing=16),
        ft.ResponsiveRow([
            ft.Container(card(ft.Column([
                ft.Row([text("Actividad de ventas", 17, True, expand=True), pill("Últimos 7 días", "blue")]),
                sales_chart(state),
            ], spacing=24)), col={"sm": 12, "lg": 8}),
            ft.Container(card(ft.Column([
                ft.Row([text("Caja de trabajo", 17, True, expand=True), pill("Abierta" if state.shift_open else "Cerrada") if state.demo else pill("Maquetado", "amber")]),
                text("Caja principal", 22, True),
                text(f"Operador: {state.user.get('nombre', '—')}", 12, color=MUTED),
                ft.Divider(color=ft.Colors.OUTLINE_VARIANT),
                ft.Row([text("Fondo de apertura", 13, color=MUTED, expand=True), text(money(state.opening_cash) if state.demo else "—", 16, True)]),
                secondary("Ver corte de caja", lambda e: app.navigate("caja/corte"), ft.Icons.POINT_OF_SALE),
                secondary("Revisar inventario", lambda e: app.navigate("inventario"), ft.Icons.INVENTORY_2_OUTLINED),
            ], spacing=18)), col={"sm": 12, "lg": 4}),
        ], spacing=16, run_spacing=16),
        card(ft.Column([
            ft.Row([text("Últimas ventas", 17, True, expand=True), ft.TextButton("Ver reporte", on_click=lambda e: app.navigate("reportes/ventas"))]),
            table(["TICKET", "FECHA", "CLIENTE", "TOTAL", "ESTADO"],
                  [[f"#{s['id_venta']}", s["fecha_hora"].replace("T", " ")[:16],
                    next((c["nombre"] for c in state.clients if c["id_cliente"] == s.get("id_cliente")), "Público general"),
                    money(s["total"]), pill(s["estado"], "green" if s["estado"] == "Completada" else "red")]
                   for s in sorted(state.sales, key=lambda s: s["fecha_hora"], reverse=True)[:5]]),
        ], spacing=16)),
    ], spacing=22)


def sales_chart(state):
    from datetime import timedelta
    days = [datetime.now().date() - timedelta(days=n) for n in range(6, -1, -1)]
    amounts = [sum(Decimal(str(s["total"])) for s in state.sales if s["fecha_hora"].startswith(day.isoformat()) and s["estado"] == "Completada") for day in days]
    highest = max(amounts, default=Decimal(1)) or Decimal(1)
    names = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
    return ft.Row([
        ft.Column([text(money(amount), 10, color=MUTED),
                   ft.Container(bgcolor=GREEN if i == 6 else "#B7D8CD", height=max(4, float(amount / highest) * 120), width=34, border_radius=5),
                   text(names[day.weekday()], 11, color=MUTED)],
                  horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.END, height=175, expand=True)
        for i, (day, amount) in enumerate(zip(days, amounts))
    ], vertical_alignment=ft.CrossAxisAlignment.END, spacing=10)


def cart_view(app):
    state = app.state
    query = ft.TextField(hint_text="Escanea un código o busca un producto", prefix_icon=ft.Icons.BARCODE_READER,
                         dense=True, border_radius=10)
    catalog = ft.Column(spacing=8)

    def search(e=None):
        value = (query.value or "").casefold()
        matches = [p for p in state.products if value in (p["nombre"] + " " + (p.get("codigo_barras") or "")).casefold()]
        catalog.controls = [ft.Container(ft.Row([
            ft.Container(ft.Icon(ft.Icons.INVENTORY_2_OUTLINED, color=GREEN, size=20), padding=12, bgcolor="#E2F3EC", border_radius=9),
            ft.Column([text(p["nombre"], 13, True), text(f"{p.get('codigo_barras') or 'Sin código'} · Stock: {p['stock_actual']}", 11, color=MUTED)], expand=True, spacing=4),
            text(money(p["precio_venta"]), 14, True),
            ft.IconButton(ft.Icons.ADD_CIRCLE_OUTLINE, icon_color=GREEN, tooltip="Añadir unidad", on_click=lambda e, product=p: app.add_to_cart(product)),
        ], spacing=12), padding=10, border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT), border_radius=10) for p in matches[:30]]
        if not matches:
            catalog.controls = [text("No se encontraron productos.", 13, color=MUTED)]
        if e:
            app.page.update()

    def scan(e):
        match = next((p for p in state.products if p.get("codigo_barras") == query.value), None)
        if match:
            app.add_to_cart(match)
        else:
            app.notify("No se encontró ese código de barras", error=True)

    query.on_change, query.on_submit = search, scan
    search()
    client = ft.Dropdown(label="Cliente", value=str(state.cart_client or "general"), dense=True, disabled=bool(app.pending_sale),
        options=[ft.DropdownOption("general", "Público general")] + [ft.DropdownOption(str(c["id_cliente"]), c["nombre"]) for c in state.clients],
        on_select=lambda e: setattr(state, "cart_client", int(e.control.value) if e.control.value != "general" else None))
    rows = []
    for p in state.products:
        quantity = state.cart.get(p["id_producto"], Decimal(0))
        if not quantity:
            continue
        product_id = p["id_producto"]
        qty = ft.TextField(value=str(quantity), width=90, dense=True, text_size=12,
                           tooltip="Cantidad: hasta 3 decimales; Enter para aplicar", on_submit=lambda e, pid=product_id: app.set_quantity(pid, e.control.value))
        rows.append([p["nombre"], qty, money(Decimal(str(p["precio_venta"])) * quantity),
                     ft.IconButton(ft.Icons.CLOSE, tooltip="Quitar producto", icon_size=17, on_click=lambda e, pid=product_id: app.remove_from_cart(pid))])
    cart = card(ft.Column([
        ft.Row([text("Ticket actual", 18, True, expand=True), pill(f"{len(state.cart)} productos", "blue")]),
        client,
        table(["PRODUCTO", "CANTIDAD", "IMPORTE", ""], rows, "Añade productos para comenzar una venta."),
        ft.Divider(color=ft.Colors.OUTLINE_VARIANT),
        ft.Row([text("Total", 16, True, expand=True), text(money(state.total), 30, True, GREEN)]),
        text("Precios finales del catálogo. El esquema actual no desglosa IVA.", 11, color=MUTED),
        primary("Cobrar venta", lambda e: checkout_dialog(app), ft.Icons.PAYMENTS_OUTLINED, disabled=not state.cart),
        secondary("Vaciar carrito", lambda e: app.empty_cart(), ft.Icons.DELETE_OUTLINE, disabled=not state.cart),
    ], spacing=18))
    return ft.Column([
        heading("Carrito", "Busca, escanea y cobra desde una sola pantalla."),
        *([note("El último cobro no tuvo confirmación. Reintenta Cobrar venta: se conserva la misma operación para evitar duplicados.")] if app.pending_sale else []),
        ft.ResponsiveRow([
            ft.Container(card(ft.Column([text("Catálogo de productos", 17, True), query, catalog], spacing=18)), col={"sm": 12, "lg": 6}),
            ft.Container(cart, col={"sm": 12, "lg": 6}),
        ], spacing=20, run_spacing=20),
        note("Las cantidades admiten hasta 3 decimales para productos a granel. Usa Enter para aplicar la cantidad."),
    ], spacing=22)


def checkout_dialog(app):
    state = app.state
    method = ft.Dropdown(label="Método de pago", value=str(state.methods[0]["id_metodo_pago"]) if state.methods else None,
                         options=[ft.DropdownOption(str(m["id_metodo_pago"]), m["nombre"]) for m in state.methods])
    if app.pending_sale:
        method.value = str(app.pending_sale["id_metodo_pago"])
        method.disabled = True
    cash = ft.TextField(label="Efectivo recibido", value=str(state.total), prefix=ft.Text("$ "))
    change = text("Cambio: $0.00", 20, True, GREEN)
    error = text("", 12, color=ft.Colors.ERROR)
    submit = primary("Confirmar cobro", None, ft.Icons.CHECK)

    def update(e=None):
        selected = next((m for m in state.methods if str(m["id_metodo_pago"]) == method.value), {})
        cash.visible = selected.get("nombre") == "Efectivo"
        change.visible = cash.visible
        try:
            value = Decimal(cash.value or "0")
            if not value.is_finite():
                raise ValueError
            change.value = f"Cambio: {money(value - state.total)}"
        except Exception:
            change.value = "Escribe un importe válido"
        if e:
            app.page.update()

    async def pay(e):
        if submit.disabled:
            return
        try:
            if not method.value:
                raise ValueError("Selecciona un método de pago")
            if cash.visible:
                value = Decimal(cash.value or "0")
                if not value.is_finite() or value < state.total or value != value.quantize(Decimal("0.01")):
                    raise ValueError("El efectivo debe cubrir el total y tener hasta 2 decimales")
            submit.disabled = True
            app.page.update()
            result = await app.checkout(int(method.value))
            app.page.pop_dialog()
            app.render()
            app.notify(f"Venta #{result['id_venta']} registrada · {money(result['total'])}" + (" · demostración" if state.demo else ""))
        except Exception as exc:
            submit.disabled = False
            error.value = str(exc)
            app.page.update()

    method.on_select, cash.on_change, submit.on_click = update, update, pay
    update()
    app.dialog("Cobrar venta", ft.Column([text(money(state.total), 36, True, GREEN), method, cash, change, error,
        note("El cobro en tarjeta es un registro del método de pago; no procesa una transacción bancaria.")], width=450, tight=True, spacing=18),
        [secondary("Volver", lambda e: app.page.pop_dialog()), submit])


def cut_view(app):
    state = app.state
    shift = state.sales[state.shift_start:]
    cash_sales = sum((Decimal(str(s["total"])) for s in shift if s["id_metodo_pago"] == 1 and s["estado"] == "Completada"), Decimal(0))
    expected = state.opening_cash + cash_sales
    counted = ft.TextField(label="Efectivo contado", prefix=ft.Text("$ "), value=str(expected), width=260)
    difference = text("Diferencia: $0.00", 22, True, GREEN)

    def calculate(e):
        try:
            amount = Decimal(counted.value or "0")
            if not amount.is_finite() or amount < 0:
                raise ValueError
            difference.value = f"Diferencia: {money(amount - expected)}"
        except Exception:
            difference.value = "Escribe un importe válido"
        app.page.update()

    def close(e):
        if not state.demo:
            app.notify("El corte está maquetado. Falta persistir turnos y movimientos de caja en el backend.")
            return
        if state.shift_open:
            try:
                amount = Decimal(counted.value or "0")
                if not amount.is_finite() or amount < 0:
                    raise ValueError
            except Exception:
                app.notify("Escribe un efectivo contado válido", error=True)
                return
        else:
            state.shift_start = len(state.sales)
        state.shift_open = not state.shift_open
        app.render()
        app.notify("Caja " + ("abierta" if state.shift_open else "cerrada") + " en la demostración")

    counted.on_change = calculate
    return ft.Column([
        heading("Corte de caja", "Revisa los cobros, cuenta el efectivo y concilia tu turno."), tabs(app, "caja"),
        note("Vista de demostración: el modelo original no contiene tablas de turnos ni movimientos de caja. Este corte no es un cierre contable persistido."),
        ft.ResponsiveRow([
            stat("Fondo inicial", money(state.opening_cash) if state.demo else "—", "Apertura del turno", ft.Icons.ACCOUNT_BALANCE_WALLET_OUTLINED),
            stat("Ventas en efectivo", money(cash_sales) if state.demo else "—", "Ingresos del turno", ft.Icons.PAYMENTS_OUTLINED),
            stat("Efectivo esperado", money(expected) if state.demo else "—", "Fondo + cobros en efectivo", ft.Icons.POINT_OF_SALE),
            stat("Tickets del turno", len(shift) if state.demo else "—", "Historial de esta sesión", ft.Icons.RECEIPT_LONG_OUTLINED),
        ], spacing=16, run_spacing=16),
        card(ft.Column([
            text("Conciliación de efectivo", 18, True), counted, difference,
            primary("Cerrar caja" if state.shift_open else "Abrir caja", close, ft.Icons.LOCK_OUTLINE, disabled=not state.demo),
        ], spacing=20)),
    ], spacing=22)
