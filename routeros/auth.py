"""
Autenticación HTTP Basic para cliente RouterOS.
"""

import base64
from typing import Tuple


class BasicAuth:
    """Generador de autenticación HTTP Basic."""

    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self._credentials = self._encode_credentials()

    def _encode_credentials(self) -> str:
        """Codifica credenciales en base64."""
        credentials = f"{self.username}:{self.password}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"

    @property
    def header(self) -> Tuple[str, str]:
        """Retorna header de autenticación."""
        return "Authorization", self._credentials

    def get_headers(self) -> dict:
        """Retorna diccionario de headers de autenticación."""
        key, value = self.header
        return {key: value}
