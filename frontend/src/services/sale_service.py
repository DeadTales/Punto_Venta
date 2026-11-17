from decimal import Decimal

from shared.receipts import receipt_pdf


class SaleService:
    def __init__(self, app):
        self.app = app

    async def detail(self, identifier):
        if not self.app.state.demo:
            return await self.app.api.request("GET", f"/api/sales/{identifier}")

        state = self.app.state
        sale = next(sale for sale in state.sales if sale["id_venta"] == identifier)
        detail = dict(state.sale_details.get(identifier, sale))
        client = next(
            (
                client
                for client in state.clients
                if client["id_cliente"] == sale.get("id_cliente")
            ),
            {},
        )
        method = next(
            (
                method
                for method in state.methods
                if method["id_metodo_pago"] == sale["id_metodo_pago"]
            ),
            {},
        )
        detail.update(
            empleado=state.user.get("nombre", "Demostración"),
            cliente=client.get("nombre", "Público general"),
            metodo_pago=method.get("nombre", "—"),
        )
        detail.setdefault("items", [])
        detail.setdefault("impuesto", "0")

        return detail

    async def pdf(self, identifier):
        if not self.app.state.demo:
            return await self.app.api.download(f"/api/sales/{identifier}/receipt")

        return receipt_pdf(await self.detail(identifier), self.app.state.business_name)

    async def cancel(self, identifier, values):
        if self.app.pending_sale:
            raise ValueError("Confirma el cobro pendiente antes de cancelar otra venta")

        if not self.app.state.demo:
            return await self.app.api.request(
                "POST", f"/api/sales/{identifier}/cancel", json=values
            )

        detail = await self.detail(identifier)

        if detail["estado"] == "Cancelada":
            return detail

        if not detail["items"]:
            raise ValueError(
                "Este ticket inicial de ejemplo no tiene partidas; cancela una venta creada en esta sesión"
            )

        if any(
            Decimal(
                str(
                    next(
                        p
                        for p in self.app.state.products
                        if p["id_producto"] == item["id_producto"]
                    )["stock_actual"]
                )
            )
            + Decimal(str(item["cantidad"]))
            > Decimal("9999999.999")
            for item in detail["items"]
        ):
            raise ValueError("La devolución supera el límite de existencias")

        for item in detail["items"]:
            product = next(
                p
                for p in self.app.state.products
                if p["id_producto"] == item["id_producto"]
            )
            product["stock_actual"] = str(
                Decimal(str(product["stock_actual"])) + Decimal(str(item["cantidad"]))
            )

        for sale in (
            next(
                sale for sale in self.app.state.sales if sale["id_venta"] == identifier
            ),
            self.app.state.sale_details[identifier],
        ):
            sale.update(estado="Cancelada", cancel_motivo=values["motivo"])

        return await self.detail(identifier)
