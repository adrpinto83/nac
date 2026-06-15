"""
Configuración de la aplicación.

Carga variables de entorno y proporciona configuración global.
"""

import os
from functools import lru_cache
from typing import Optional


class Settings:
    """Configuración de la aplicación."""

    # App
    APP_NAME: str = "MikroTik NAC System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

    # Router
    ROUTER_IP: str = os.getenv("ROUTER_IP", "192.168.88.1")
    ROUTER_PORT: int = int(os.getenv("ROUTER_PORT", "80"))
    ROUTER_USER: str = os.getenv("ROUTER_USER", "api-container")
    ROUTER_PASSWORD: str = os.getenv("ROUTER_PASSWORD", "NAC_MikroTik_2025")
    ROUTER_VERIFY_SSL: bool = os.getenv("ROUTER_VERIFY_SSL", "False").lower() == "true"

    # Base de datos
    DATABASE_URL: str = os.getenv("DATABASE_URL", "data/db.sqlite3")

    # JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRATION_MINUTES", "1440"))

    # CORS
    CORS_ORIGINS: list = ["http://localhost:8080", "http://localhost:3000"]

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Scheduler
    TRAFFIC_SYNC_INTERVAL: int = int(os.getenv("TRAFFIC_SYNC_INTERVAL", "300"))
    EXPIRY_CHECK_INTERVAL: int = int(os.getenv("EXPIRY_CHECK_INTERVAL", "600"))
    HEALTH_CHECK_INTERVAL: int = int(os.getenv("HEALTH_CHECK_INTERVAL", "60"))

    # Validaciones
    @property
    def router_url(self) -> str:
        """URL del router."""
        return f"http://{self.ROUTER_IP}:{self.ROUTER_PORT}"

    @property
    def database_path(self) -> str:
        """Ruta de la base de datos."""
        return self.DATABASE_URL if self.DATABASE_URL.startswith("/") else self.DATABASE_URL


@lru_cache()
def get_settings() -> Settings:
    """Obtiene configuración global (cached)."""
    return Settings()
