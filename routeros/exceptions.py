"""
Excepciones tipadas para cliente RouterOS.
"""


class RouterOSException(Exception):
    """Excepción base para errores de RouterOS."""
    pass


class RouterOSConnectionError(RouterOSException):
    """Error de conexión al router."""

    def __init__(self, host: str, port: int, reason: str):
        self.host = host
        self.port = port
        self.reason = reason
        super().__init__(f"No se puede conectar a {host}:{port} - {reason}")


class RouterOSAuthError(RouterOSException):
    """Error de autenticación (401)."""

    def __init__(self, username: str):
        self.username = username
        super().__init__(f"Autenticación fallida para usuario {username}")


class RouterOSNotFoundError(RouterOSException):
    """Recurso no encontrado (404)."""

    def __init__(self, endpoint: str):
        self.endpoint = endpoint
        super().__init__(f"Endpoint no encontrado: {endpoint}")


class RouterOSValidationError(RouterOSException):
    """Error de validación (422)."""

    def __init__(self, endpoint: str, details: dict):
        self.endpoint = endpoint
        self.details = details
        super().__init__(f"Validación fallida en {endpoint}: {details}")


class RouterOSServerError(RouterOSException):
    """Error del servidor (500)."""

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"Error del servidor ({status_code}): {message}")


class RouterOSTimeoutError(RouterOSException):
    """Timeout de conexión."""

    def __init__(self, timeout_seconds: float):
        self.timeout_seconds = timeout_seconds
        super().__init__(f"Timeout después de {timeout_seconds} segundos")


class RouterOSInvalidResponseError(RouterOSException):
    """Respuesta inválida del router."""

    def __init__(self, reason: str):
        super().__init__(f"Respuesta inválida del router: {reason}")
