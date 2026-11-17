from datetime import datetime, time, timedelta
from decimal import ROUND_CEILING, ROUND_HALF_UP, Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select

from ...core.config.db_config import get_session
from ...core.security import current_user
from ..entities import Product, Sale, SaleDetail

router = APIRouter(
    prefix="/api/reports", tags=["Reportes"], dependencies=[Depends(current_user)]
)


@router.get("/products")
async def product_demand(
    days: int = Query(30, ge=1, le=365),
    lead_days: int = Query(7, ge=1, le=90),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    session=Depends(get_session, scope="function"),
):
    since = datetime.combine(datetime.now().date() - timedelta(days=days - 1), time.min)
    sold = (
        select(SaleDetail.id_producto, func.sum(SaleDetail.cantidad).label("cantidad"))
        .join(Sale, Sale.id_venta == SaleDetail.id_venta)
        .where(Sale.estado == "Completada", Sale.fecha_hora >= since)
        .group_by(SaleDetail.id_producto)
        .subquery()
    )
    statement = (
        select(Product, func.coalesce(sold.c.cantidad, 0))
        .outerjoin(sold, sold.c.id_producto == Product.id_producto)
        .order_by(Product.nombre, Product.id_producto)
        .limit(limit)
        .offset(offset)
    )
    rows = (await session.execute(statement)).all()
    result = []

    for product, quantity in rows:
        daily = Decimal(quantity) / days
        target = max(product.stock_minimo, daily * lead_days)
        suggested = max(Decimal(0), target - product.stock_actual).quantize(
            Decimal("0.001"), rounding=ROUND_CEILING
        )
        result.append(
            {
                "id_producto": product.id_producto,
                "nombre": product.nombre,
                "cantidad_vendida": str(quantity),
                "promedio_diario": str(
                    daily.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
                ),
                "stock_actual": str(product.stock_actual),
                "reposicion_sugerida": str(suggested),
                "dias_periodo": days,
                "dias_cobertura": lead_days,
            }
        )

    return result
