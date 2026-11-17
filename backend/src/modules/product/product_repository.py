from sqlalchemy import or_, select

from ...core.repository import Repository
from .product_model import Product


class ProductRepository(Repository):
    def __init__(self, session):
        super().__init__(session, Product)

    async def get_by_barcode(self, code):
        statement = select(Product).where(Product.codigo_barras == code)

        return await self.session.scalar(statement)

    async def barcode_exists(self, code, excluding_id=None):
        statement = select(Product.id_producto).where(Product.codigo_barras == code)

        if excluding_id is not None:
            statement = statement.where(Product.id_producto != excluding_id)

        return await self.session.scalar(statement) is not None

    async def existing_barcodes(self, codes):
        if not codes:
            return set()

        statement = select(Product.codigo_barras).where(
            Product.codigo_barras.in_(codes)
        )
        barcodes = await self.session.scalars(statement)

        return set(barcodes.all())

    async def search(
        self, query="", low_stock=False, limit=100, offset=0, category_id=None
    ):
        statement = select(Product).order_by(Product.nombre, Product.id_producto)

        if query:
            # autoescape evita que % y _ introducidos por el usuario sean comodines.
            statement = statement.where(
                or_(
                    Product.nombre.icontains(query, autoescape=True),
                    Product.codigo_barras.icontains(query, autoescape=True),
                )
            )

        if low_stock:
            statement = statement.where(Product.stock_actual <= Product.stock_minimo)

        if category_id is not None:
            statement = statement.where(Product.id_categoria == category_id)

        return list(
            (await self.session.scalars(statement.limit(limit).offset(offset))).all()
        )
