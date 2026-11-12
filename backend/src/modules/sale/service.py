from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json

from fastapi import HTTPException
from sqlalchemy import select, text

from ..entities import Client, Employee, PaymentMethod, Product, Sale, SaleDetail


def fingerprint(payload):
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


async def lock_operation(session, identifier):
    # Serializa reintentos de un mismo UUID incluso entre procesos de la API.
    key = int.from_bytes(hashlib.sha256(str(identifier).encode()).digest()[:8], signed=True)
    await session.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": key})


async def record_sale(session, identifier, employee, client, method, lines, request_hash, date=None):
    """Bloquea artículos en orden estable; precio congelado sólo en recepción sync."""
    await lock_operation(session, identifier)
    existing = await session.scalar(select(Sale).where(Sale.sync_id == identifier))
    if existing:
        if existing.request_hash != request_hash:
            raise HTTPException(409, "La clave de operación ya se usó con otros datos")
        return existing, False
    ids = [line[0] for line in lines]
    if len(ids) != len(set(ids)):
        raise HTTPException(422, "Agrupa las cantidades de cada producto en una sola línea")
    products = {p.id_producto: p for p in (await session.scalars(
        select(Product).where(Product.id_producto.in_(ids)).order_by(Product.id_producto).with_for_update()
    )).all()}
    if len(products) != len(ids):
        raise HTTPException(422, "Algún producto ya no existe")
    sale = Sale(sync_id=identifier, id_empleado=employee.id_empleado,
                id_cliente=client.id_cliente if client else None, id_metodo_pago=method.id_metodo_pago,
                fecha_hora=date or datetime.now(), total=Decimal(0), estado="Completada", request_hash=request_hash)
    session.add(sale)
    await session.flush()
    total = Decimal(0)
    for product_id, quantity, frozen_price in lines:
        product = products[product_id]
        if product.stock_actual < quantity:
            raise HTTPException(409, f"Stock insuficiente para {product.nombre}. No se guardó la venta.")
        price = frozen_price if frozen_price is not None else product.precio_venta
        subtotal = (price * quantity).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        total += subtotal
        if total > Decimal("99999999.99"):
            raise HTTPException(422, "El total supera el límite de la base de datos")
        product.stock_actual -= quantity
        session.add(SaleDetail(id_venta=sale.id_venta, id_producto=product_id,
            cantidad=quantity, precio_unitario_venta=price, subtotal=subtotal))
    sale.total = total
    await session.flush()
    return sale, True


async def create_sale(session, body, employee, queue_sync=False):
    client = await session.get(Client, body.id_cliente) if body.id_cliente else None
    method = await session.get(PaymentMethod, body.id_metodo_pago)
    if not method or body.id_cliente and not client:
        raise HTTPException(422, "Cliente o método de pago no válido")
    digest = fingerprint({**body.model_dump(mode="json"), "employee": str(employee.sync_id)})
    sale, created = await record_sale(session, body.operation_id, employee, client, method,
        [(line.id_producto, line.cantidad, None) for line in body.items], digest)
    if created and queue_sync:
        from ..sync.service import enqueue
        details = (await session.execute(select(SaleDetail, Product).join(Product, SaleDetail.id_producto == Product.id_producto)
            .where(SaleDetail.id_venta == sale.id_venta))).all()
        await enqueue(session, "sale.completed", {
            "sync_id": str(sale.sync_id), "employee_sync_id": str(employee.sync_id),
            "client_sync_id": str(client.sync_id) if client else None,
            "payment_method": method.nombre, "fecha_hora": sale.fecha_hora.isoformat(),
            "items": [{"product_sync_id": str(p.sync_id), "cantidad": str(d.cantidad),
                       "precio_unitario_venta": str(d.precio_unitario_venta)} for d, p in details],
        })
    return sale


async def receive_sale(session, snapshot):
    employee = await session.scalar(select(Employee).where(Employee.sync_id == snapshot.employee_sync_id))
    client = await session.scalar(select(Client).where(Client.sync_id == snapshot.client_sync_id)) if snapshot.client_sync_id else None
    method = await session.scalar(select(PaymentMethod).where(PaymentMethod.nombre == snapshot.payment_method))
    if not employee or not method or snapshot.client_sync_id and not client:
        raise HTTPException(409, "Faltan empleado, cliente o método de pago en la nube. Aprovisiona los mismos UUID antes de sincronizar.")
    products = {p.sync_id: p.id_producto for p in (await session.scalars(select(Product).where(
        Product.sync_id.in_([line.product_sync_id for line in snapshot.items])
    ))).all()}
    if any(line.product_sync_id not in products for line in snapshot.items):
        raise HTTPException(409, "Faltan productos del catálogo en la nube")
    try:
        date = datetime.fromisoformat(snapshot.fecha_hora)
        if date.tzinfo is not None:
            raise ValueError
    except ValueError:
        raise HTTPException(422, "fecha_hora debe ser una fecha ISO local sin zona, conforme al esquema original") from None
    return await record_sale(session, snapshot.sync_id, employee, client, method,
        [(products[line.product_sync_id], line.cantidad, line.precio_unitario_venta) for line in snapshot.items],
        fingerprint(snapshot.model_dump(mode="json")), date)
