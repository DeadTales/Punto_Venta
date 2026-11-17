"""Captura el frontend real con fixtures aislados para el manual de usuario."""

import argparse
import asyncio
import base64
import json
import subprocess
import sys
from pathlib import Path

import httpx
from websockets.asyncio.client import connect

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / ".venv-codex"
OUTPUT = ROOT / "docs/manual/capturas"
SERVER_URL = "http://127.0.0.1:8767"
BROWSER_URL = "http://127.0.0.1:9227"
SCENES = (
    "login",
    "inicio",
    "buscar_vista",
    "caja_cerrada",
    "abrir_caja",
    "carrito",
    "cobrar",
    "tickets",
    "ticket",
    "cancelar_venta",
    "clientes",
    "cliente_formulario",
    "inventario",
    "producto_formulario",
    "categorias",
    "categoria_formulario",
    "ajustes",
    "ajuste_formulario",
    "eliminar_producto",
    "importar",
    "importar_validado",
    "corte",
    "cerrar_caja",
    "usuarios",
    "usuario_formulario",
    "desactivar_usuario",
    "reporte_ventas",
    "reporte_predicciones",
    "perifericos",
    "aspectos",
    "contrasena",
    "correo",
    "perifericos_serial",
    "perifericos_red",
    "sesion",
    "inventario_pie",
    "reporte_tabla",
)


class Browser:
    def __init__(self, socket):
        self.socket = socket
        self.identifier = 0

    async def command(self, method, params=None):
        self.identifier += 1
        await self.socket.send(
            json.dumps(
                {"id": self.identifier, "method": method, "params": params or {}}
            )
        )

        while True:
            result = json.loads(await asyncio.wait_for(self.socket.recv(), 25))

            if result.get("id") != self.identifier:
                continue

            if "error" in result:
                raise RuntimeError(str(result["error"]))

            return result.get("result", {})


async def wait_for_server(client):
    for _ in range(40):
        try:
            response = await client.get(SERVER_URL + "/__manual/ready")

            if response.status_code == 200:
                return
        except httpx.HTTPError:
            pass

        await asyncio.sleep(0.5)

    raise RuntimeError("No arrancó el servidor local de capturas")


async def find_browser(client):
    for _ in range(40):
        try:
            targets = (await client.get(BROWSER_URL + "/json/list")).json()
            target = next((item for item in targets if item["type"] == "page"), None)

            if target:
                return target
        except httpx.HTTPError:
            pass

        await asyncio.sleep(0.5)

    raise RuntimeError("No arrancó el navegador aislado")


async def capture_scenes(client, browser, scenes):
    await browser.command(
        "Emulation.setDeviceMetricsOverride",
        {"width": 1440, "height": 1080, "deviceScaleFactor": 1, "mobile": False},
    )

    for _ in range(90):
        response = await client.get(SERVER_URL + "/__manual/ready")

        if response.json()["ready"]:
            break

        await asyncio.sleep(1)
    else:
        raise RuntimeError("Flet no terminó de cargar")

    await asyncio.sleep(2)

    for scene in scenes:
        response = await client.post(
            SERVER_URL + "/__manual/scene/" + scene, timeout=20
        )
        response.raise_for_status()
        await asyncio.sleep(1.2)
        result = await browser.command("Page.captureScreenshot", {"format": "png"})
        (OUTPUT / f"{scene}.png").write_bytes(base64.b64decode(result["data"]))
        print(f"Captura real guardada: {scene}", flush=True)


async def main(scenes):
    WORK.mkdir(exist_ok=True)
    OUTPUT.mkdir(parents=True, exist_ok=True)

    with (WORK / "manual-preview.log").open("w", encoding="utf-8") as server_log:
        with (WORK / "manual-browser.log").open("w", encoding="utf-8") as browser_log:
            server = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "uvicorn",
                    "manual_preview:app",
                    "--app-dir",
                    str(Path(__file__).resolve().parent),
                    "--host",
                    "127.0.0.1",
                    "--port",
                    "8767",
                ],
                cwd=ROOT,
                stdout=server_log,
                stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            process = None

            try:
                async with httpx.AsyncClient(trust_env=False, timeout=3) as client:
                    await wait_for_server(client)
                    process = subprocess.Popen(
                        [
                            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                            "--headless=new",
                            "--no-first-run",
                            "--no-default-browser-check",
                            "--disable-background-networking",
                            "--disable-component-update",
                            "--enable-unsafe-swiftshader",
                            "--use-angle=swiftshader",
                            "--remote-debugging-port=9227",
                            "--remote-debugging-address=127.0.0.1",
                            f"--user-data-dir={WORK / 'manual-browser-profile'}",
                            "--window-size=1440,1080",
                            SERVER_URL,
                        ],
                        stdout=browser_log,
                        stderr=subprocess.STDOUT,
                        creationflags=subprocess.CREATE_NO_WINDOW,
                    )
                    target = await find_browser(client)

                    async with connect(
                        target["webSocketDebuggerUrl"], max_size=30_000_000
                    ) as socket:
                        browser = Browser(socket)
                        await capture_scenes(client, browser, scenes)
                        await browser.command("Browser.close")
            finally:
                for child in (process, server):
                    if child and child.poll() is None:
                        child.terminate()

                        try:
                            child.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            child.kill()
                            child.wait(timeout=5)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scenes", nargs="*", metavar="SCENE")
    arguments = parser.parse_args()

    if invalid := set(arguments.scenes) - set(SCENES):
        parser.error("Escenas desconocidas: " + ", ".join(sorted(invalid)))

    asyncio.run(main(arguments.scenes or SCENES))
