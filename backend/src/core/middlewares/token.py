"""Acceso común a las dependencias JWT; implementación en core.security."""
from ..security import current_user, roles

__all__ = ["current_user", "roles"]
