from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from uuid import uuid4


def money(value):
    return f"${Decimal(str(value)):,.2f}"


@dataclass
class AppState:
    mode: str = "demo"
    products: list[dict] = field(default_factory=list)
    categories: list[dict] = field(default_factory=list)
    clients: list[dict] = field(default_factory=list)
    users: list[dict] = field(default_factory=list)
    sales: list[dict] = field(default_factory=list)
    methods: list[dict] = field(default_factory=list)
    user: dict = field(default_factory=dict)
    cart: dict[int, Decimal] = field(default_factory=dict)
    cart_client: int | None = None
    operation_id: str = field(default_factory=lambda: str(uuid4()))
    shift_open: bool = True
    opening_cash: Decimal = Decimal("1000")
    shift_start: int = 0
    sync: dict = field(default_factory=dict)
    theme: str = "light"
    peripheral: str = "USB"

    @property
    def demo(self):
        return self.mode == "demo"

    @property
    def total(self):
        return sum(((Decimal(str(p["precio_venta"])) * self.cart.get(p["id_producto"], Decimal(0)))
                    .quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                    for p in self.products), Decimal(0))

    @property
    def low_stock(self):
        return [p for p in self.products if Decimal(str(p["stock_actual"])) <= Decimal(str(p["stock_minimo"]))]

    def reset_cart(self):
        self.cart.clear()
        self.cart_client = None
        self.operation_id = str(uuid4())
