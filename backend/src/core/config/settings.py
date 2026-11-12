"""Configuración explícita: nunca cambiar de base durante una transacción."""
from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    database_url: str
    database_mode: str = "cloud"
    pool_size: int = 5
    max_overflow: int = 5
    jwt_secret: str = ""
    sync_url: str = ""
    sync_key: str = ""
    sync_interval: float = 30

    @classmethod
    def from_env(cls):
        load_dotenv(Path(__file__).resolve().parents[3] / ".env")
        mode = os.getenv("DATABASE_MODE", "cloud")
        if mode not in {"cloud", "local"}:
            raise ValueError("DATABASE_MODE debe ser cloud o local")
        name = "LOCAL_DATABASE_URL" if mode == "local" else "DATABASE_URL"
        url = os.getenv(name, "")
        if not url:
            raise ValueError(f"Falta {name}. Consulta backend/.env.example")
        secret = os.getenv("JWT_SECRET", "")
        if len(secret) < 32:
            raise ValueError("Configura JWT_SECRET con al menos 32 caracteres aleatorios")
        sync_key = os.getenv("SYNC_KEY", "")
        if sync_key and len(sync_key) < 32:
            raise ValueError("SYNC_KEY debe tener al menos 32 caracteres aleatorios")
        pool_size = int(os.getenv("DB_POOL_SIZE", "5"))
        max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "5"))
        if pool_size < 1 or max_overflow < 0:
            raise ValueError("DB_POOL_SIZE debe ser positivo y DB_MAX_OVERFLOW no negativo")
        return cls(
            database_url=url, database_mode=mode, jwt_secret=secret,
            pool_size=pool_size, max_overflow=max_overflow,
            sync_url=os.getenv("SYNC_API_URL", "").rstrip("/"),
            sync_key=sync_key,
            sync_interval=max(5, float(os.getenv("SYNC_INTERVAL", "30"))),
        )
