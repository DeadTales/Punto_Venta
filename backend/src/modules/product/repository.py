from sqlalchemy import or_, select

from ...core.repository import Repository
from .models import Product


class ProductRepository(Repository):
    def __init__(self, session):
        super().__init__(session, Product)

    async def search(self, query="", low_stock=False, limit=100, offset=0):
        statement = select(Product).order_by(Product.nombre, Product.id_producto)
        if query:
            # autoescape evita que % y _ introducidos por el usuario sean comodines.
            statement = statement.where(or_(
                Product.nombre.icontains(query, autoescape=True),
                Product.codigo_barras.icontains(query, autoescape=True),
            ))
        if low_stock:
            statement = statement.where(Product.stock_actual <= Product.stock_minimo)
        return list((await self.session.scalars(statement.limit(limit).offset(offset))).all())
