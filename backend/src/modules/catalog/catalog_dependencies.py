"""Decisiones comunes de las dependencias HTTP."""

from fastapi import Request


def should_queue_sync(request: Request) -> bool:
    return request.app.state.settings.database_mode == "local"
