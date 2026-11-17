"""Consultas de categorías sin cerrar la transacción del servicio."""

from collections import Counter

from sqlalchemy import func, select

from ...core.repository import Repository
from .category_model import Category


class CategoryRepository(Repository):
    def __init__(self, session):
        super().__init__(session, Category)

    async def get_for_product(self, identifier):
        statement = (
            select(Category)
            .where(Category.id_categoria == identifier)
            .with_for_update(read=True)
        )

        return await self.session.scalar(statement)

    async def name_exists(self, name, excluding_id=None):
        statement = select(Category.id_categoria).where(
            func.lower(func.trim(Category.nombre)) == name.lower()
        )

        if excluding_id is not None:
            statement = statement.where(Category.id_categoria != excluding_id)

        return await self.session.scalar(statement) is not None

    async def count_by_names(self, names):
        statement = select(Category.nombre).where(Category.nombre.in_(names))
        matching_names = await self.session.scalars(statement)

        return Counter(matching_names.all())

    async def all_by_name(self):
        categories = await self.session.scalars(select(Category))

        return {category.nombre: category for category in categories.all()}
