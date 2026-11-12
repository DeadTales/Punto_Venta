"""Datos exclusivamente del maquetado; nunca se envían a la API."""
from datetime import datetime, timedelta

from .state import AppState


def demo_state():
    state = AppState()
    state.user = {"nombre": "Andrea", "apellido": "García", "correo": "andrea@ejemplo.local", "rol": "Administrador"}
    state.categories = [{"id_categoria": i + 1, "nombre": name} for i, name in enumerate(["General", "Bebidas", "Abarrotes", "Limpieza"])]
    entries = [
        ("7501000000011", "Agua natural · 600 ml", 2, "6.50", "12.00", "48", "12"),
        ("7501000000028", "Café molido · 250 g", 3, "42.00", "68.00", "8", "10"),
        ("7501000000035", "Leche entera · 1 L", 3, "19.00", "26.50", "32", "8"),
        ("7501000000042", "Galletas de avena", 3, "10.00", "18.00", "5", "10"),
        ("7501000000059", "Jabón líquido · 500 ml", 4, "24.00", "39.00", "18", "5"),
        ("0012345678901", "Arroz a granel · kg", 3, "18.00", "29.90", "24.750", "5"),
        ("7501000000073", "Jugo de naranja · 1 L", 2, "21.00", "34.00", "16", "6"),
        ("7501000000080", "Bolsa reutilizable", 1, "4.00", "10.00", "60", "15"),
    ]
    keys = ("codigo_barras", "nombre", "id_categoria", "precio_compra", "precio_venta", "stock_actual", "stock_minimo")
    state.products = [{"id_producto": i + 1, **dict(zip(keys, row))} for i, row in enumerate(entries)]
    state.clients = [
        {"id_cliente": 1, "nombre": "María López", "telefono": "55 1234 5678", "correo": "maria@ejemplo.local", "rfc_o_identificacion_fiscal": "LOPM900101ABC"},
        {"id_cliente": 2, "nombre": "Cafetería Central", "telefono": "55 8765 4321", "correo": "compras@ejemplo.local", "rfc_o_identificacion_fiscal": "CCE120315XYZ"},
        {"id_cliente": 3, "nombre": "Jorge Hernández", "telefono": "55 2468 1357", "correo": "jorge@ejemplo.local", "rfc_o_identificacion_fiscal": None},
    ]
    state.users = [
        {"id_empleado": 1, **state.user},
        {"id_empleado": 2, "nombre": "Luis", "apellido": "Mendoza", "correo": "luis@ejemplo.local", "rol": "Cajero", "telefono": "55 1122 3344"},
        {"id_empleado": 3, "nombre": "Valeria", "apellido": "Soto", "correo": "valeria@ejemplo.local", "rol": "Supervisor", "telefono": "55 5566 7788"},
    ]
    state.methods = [{"id_metodo_pago": i + 1, "nombre": name} for i, name in enumerate(["Efectivo", "Tarjeta Débito", "Tarjeta Crédito", "Transferencia"])]
    today = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)
    state.sales = [{"id_venta": i + 1001, "fecha_hora": (today - timedelta(days=6 - i)).isoformat(),
                    "id_cliente": i % 3 + 1, "id_empleado": i % 3 + 1, "id_metodo_pago": i % 4 + 1,
                    "total": amount, "estado": "Completada"}
                   for i, amount in enumerate(["1250.50", "1820.00", "1535.00", "2240.50", "1980.00", "2680.00", "2364.50"])]
    state.shift_start = 6
    return state
