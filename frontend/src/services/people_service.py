from shared.people import ClientInput, EmployeeCreate, EmployeeUpdate


class PeopleService:
    def __init__(self, app):
        self.app = app

    async def save(self, values, users=False, identifier=None):
        if (
            users
            and not self.app.state.demo
            and self.app.state.user.get("rol") != "Administrador"
        ):
            raise ValueError("Sólo el Administrador puede gestionar empleados")

        schema = (
            EmployeeCreate
            if users and identifier is None
            else EmployeeUpdate
            if users
            else ClientInput
        )
        body = schema.model_validate(values).model_dump(mode="json")
        entity = "employees" if users else "clients"

        if not self.app.state.demo:
            return await self.app.api.request(
                "POST" if identifier is None else "PUT",
                f"/api/{entity}"
                if identifier is None
                else f"/api/{entity}/{identifier}",
                json=body,
            )

        items = self.app.state.users if users else self.app.state.clients
        key = "id_empleado" if users else "id_cliente"
        body.pop("password", None)

        if users and any(
            item.get("correo", "").lower() == body["correo"] and item[key] != identifier
            for item in items
        ):
            raise ValueError("Ya existe un empleado con ese correo")

        if identifier is None:
            record = {key: max((item[key] for item in items), default=0) + 1}
            items.append(record)
        else:
            record = next(item for item in items if item[key] == identifier)

        record.update(body)

        return record

    async def delete(self, identifier, users=False):
        entity = "employees" if users else "clients"

        if not self.app.state.demo:
            return await self.app.api.request("DELETE", f"/api/{entity}/{identifier}")

        state = self.app.state

        if users:
            record = next(
                item for item in state.users if item["id_empleado"] == identifier
            )

            if record.get("correo") == state.user.get("correo"):
                raise ValueError("No puedes desactivar tu propia cuenta")

            record["activo"] = False
        else:
            if any(sale.get("id_cliente") == identifier for sale in state.sales):
                raise ValueError("El cliente tiene ventas registradas")

            state.clients[:] = [
                item for item in state.clients if item["id_cliente"] != identifier
            ]

        return {"deleted": True}
