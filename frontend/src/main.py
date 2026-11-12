"""Ejecutar desde la raíz: python -m frontend.src.main"""
from pathlib import Path
import os
import sys

# También admite `flet run frontend/src/main.py` y `python frontend/src/main.py`.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import flet as ft
from dotenv import load_dotenv

from frontend.src.app import PosApp


async def main(page: ft.Page):
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    app = PosApp(page, os.getenv("POS_MODE", "demo"), os.getenv("API_BASE_URL", "http://127.0.0.1:8000"))
    # Conserva el controlador y los servicios mientras vive la página.
    page.data = app


if __name__ == "__main__":
    ft.run(main)
