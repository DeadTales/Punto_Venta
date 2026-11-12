"""Reexportaciones por dominio: una sola definición ORM y una sola Base."""
from ..entities import Category, Product

__all__ = ["Category", "Product"]
