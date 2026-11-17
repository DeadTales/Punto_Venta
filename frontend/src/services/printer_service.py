"""Preferencias locales y adaptadores ESC/POS para USB, serial y red."""

import asyncio
import json
from pathlib import Path

from shared.receipts import receipt_lines


class PrinterService:
    def __init__(self, path=None):
        self.path = (
            Path(path)
            if path
            else Path(__file__).resolve().parents[2] / ".pos_settings.json"
        )
        self.config = {
            "connection": "USB",
            "vendor_id": "",
            "product_id": "",
            "address": "",
            "port": 9100,
            "baudrate": 9600,
            "cut": True,
        }
        self.theme = "light"

        if self.path.exists():
            try:
                values = json.loads(self.path.read_text(encoding="utf-8"))
                self.config.update(
                    {
                        key: values.get("printer", {}).get(key, default)
                        for key, default in self.config.items()
                    }
                )
                self.theme = values.get("theme", "light")
            except (ValueError, OSError, AttributeError):
                pass

    def save(self, config=None, theme=None):
        if config is not None:
            self.config = {**self.config, **config}

        if theme is not None:
            self.theme = theme

        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(
                {"printer": self.config, "theme": self.theme},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        temporary.replace(self.path)

    async def print_sale(self, sale, business_name):
        return await asyncio.to_thread(self._print, sale, business_name)

    def _print(self, sale, business_name):
        from escpos.printer import Network, Serial, Usb

        settings = self.config
        connection = settings["connection"]

        if connection == "USB":
            if not settings["vendor_id"] or not settings["product_id"]:
                raise ValueError("Configura los identificadores USB en Periféricos")

            printer = Usb(
                int(str(settings["vendor_id"]), 0),
                int(str(settings["product_id"]), 0),
                timeout=3000,
            )
        elif connection == "Serial / COM":
            if not settings["address"].strip():
                raise ValueError("Configura el puerto COM o dispositivo serial")

            printer = Serial(
                devfile=settings["address"],
                baudrate=int(settings["baudrate"]),
                timeout=3,
            )
        elif connection == "Red / Ethernet":
            if not settings["address"].strip():
                raise ValueError("Configura la dirección de la impresora")

            printer = Network(
                settings["address"], port=int(settings["port"]), timeout=5
            )
        else:
            raise ValueError("Selecciona USB, Serial / COM o Red / Ethernet")

        try:
            printer.text("\n".join(receipt_lines(sale, business_name)) + "\n\n\n")

            if settings["cut"]:
                printer.cut()
        finally:
            printer.close()
