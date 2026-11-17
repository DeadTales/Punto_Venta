"""Catálogo HTTP y operaciones equivalentes en la demostración en memoria."""

from copy import deepcopy
from urllib.parse import quote

from shared.catalog import (
    CategoryInput,
    ProductCreate,
    ProductUpdate,
    StockAdjustmentInput,
    adjusted_stock,
)

from .api_client import ApiError


class ProductService:
    def __init__(self, app):
        self.app = app
        self.demo_adjustments = {}

    @property
    def can_manage(self):
        return self.app.state.demo or self.app.state.user.get("rol") in {
            "Administrador",
            "Supervisor",
        }

    def check_write(self):
        if not self.can_manage:
            raise ValueError("Esta operación requiere Administrador o Supervisor")

        if self.app.pending_sale:
            raise ValueError(
                "Confirma el cobro pendiente antes de modificar el inventario"
            )

    async def all_products(self):
        # Conserva todos los artículos para caja/reportes aunque haya más de 500.
        result, offset = [], 0

        while True:
            page = await self.app.api.request(
                "GET", "/api/products", params={"limit": 500, "offset": offset}
            )
            result.extend(page)

            if len(page) < 500:
                return result

            offset += len(page)

    async def barcode(self, code):
        code = code.strip()

        if not code:
            raise ValueError("Escanea o escribe un código de barras")

        if not self.app.state.demo:
            return await self.app.api.request(
                "GET", "/api/products/barcode/" + quote(code, safe="")
            )

        product = next(
            (p for p in self.app.state.products if p.get("codigo_barras") == code), None
        )

        if product is None:
            raise ValueError("No existe un producto con ese código de barras")

        return product

    async def save_product(self, values, identifier=None):
        self.check_write()
        body = (
            ProductUpdate if identifier is not None else ProductCreate
        ).model_validate(values)

        if not self.app.state.demo:
            return await self.app.api.request(
                "PUT" if identifier is not None else "POST",
                f"/api/products/{identifier}"
                if identifier is not None
                else "/api/products",
                json=body.model_dump(mode="json"),
            )

        state = self.app.state

        if not any(c["id_categoria"] == body.id_categoria for c in state.categories):
            raise ValueError("Selecciona una categoría existente")

        if body.codigo_barras and any(
            p.get("codigo_barras") == body.codigo_barras
            and p["id_producto"] != identifier
            for p in state.products
        ):
            raise ValueError("El código de barras ya está registrado")

        if identifier is None:
            record = {
                "id_producto": max(
                    (p["id_producto"] for p in state.products), default=0
                )
                + 1
            }
            state.products.append(record)
        else:
            record = next(p for p in state.products if p["id_producto"] == identifier)

        record.update(body.model_dump(mode="json"))

        return record

    async def save_category(self, values, identifier=None):
        self.check_write()
        body = CategoryInput.model_validate(values)

        if not self.app.state.demo:
            return await self.app.api.request(
                "PUT" if identifier is not None else "POST",
                f"/api/categories/{identifier}"
                if identifier is not None
                else "/api/categories",
                json=body.model_dump(mode="json"),
            )

        state = self.app.state

        if any(
            c["nombre"].strip().casefold() == body.nombre.casefold()
            and c["id_categoria"] != identifier
            for c in state.categories
        ):
            raise ValueError("Ya existe una categoría con ese nombre")

        if identifier is None:
            record = {
                "id_categoria": max(
                    (c["id_categoria"] for c in state.categories), default=0
                )
                + 1
            }
            state.categories.append(record)
        else:
            record = next(
                c for c in state.categories if c["id_categoria"] == identifier
            )

        record.update(body.model_dump(mode="json"))

        return record

    async def delete(self, entity, identifier):
        self.check_write()

        if entity == "products" and identifier in self.app.state.cart:
            raise ValueError("Quita el producto del carrito antes de eliminarlo")

        if not self.app.state.demo:
            return await self.app.api.request("DELETE", f"/api/{entity}/{identifier}")

        state = self.app.state

        if entity == "categories":
            if any(p["id_categoria"] == identifier for p in state.products):
                raise ValueError(
                    "No puedes eliminar una categoría que contiene productos"
                )

            state.categories[:] = [
                c for c in state.categories if c["id_categoria"] != identifier
            ]
        else:
            if any(
                record["id_producto"] == identifier
                for record in self.demo_adjustments.values()
            ):
                raise ValueError(
                    "El producto tiene ajustes registrados; conserva su historial"
                )

            if identifier in state.demo_sold_products:
                raise ValueError(
                    "El producto tiene ventas registradas; conserva su historial"
                )

            state.products[:] = [
                p for p in state.products if p["id_producto"] != identifier
            ]

        return {"deleted": True}

    async def adjust_stock(self, identifier, values):
        self.check_write()
        body = StockAdjustmentInput.model_validate(values)

        if not self.app.state.demo:
            return await self.app.api.request(
                "POST",
                f"/api/products/{identifier}/stock-adjustments",
                json=body.model_dump(mode="json"),
            )

        payload = {"id_producto": identifier, **body.model_dump(mode="json")}
        key = str(body.operation_id)

        if key in self.demo_adjustments:
            existing = self.demo_adjustments[key]

            if existing["payload"] != payload:
                raise ValueError("La clave de operación ya se usó con otros datos")

            return existing

        product = next(
            p for p in self.app.state.products if p["id_producto"] == identifier
        )
        new_stock = adjusted_stock(product["stock_actual"], body.cantidad)
        result = {
            **payload,
            "stock_anterior": str(product["stock_actual"]),
            "stock_nuevo": str(new_stock),
            "payload": deepcopy(payload),
        }
        product["stock_actual"] = str(new_stock)
        self.demo_adjustments[key] = result

        return result

    async def refresh_after_write(self):
        if not self.app.state.demo:
            try:
                await self.app.reload()
                self.app.catalog_stale = False
            except ApiError:
                # La escritura ya terminó: no ofrecer repetirla por un fallo de lectura.
                self.app.catalog_stale = True
