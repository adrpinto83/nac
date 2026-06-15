"""Esquemas Pydantic comunes."""

from pydantic import BaseModel
from typing import Optional, Generic, TypeVar, List, Any
from datetime import datetime

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Parámetros de paginación."""
    skip: int = 0
    limit: int = 50


class PaginatedResponse(BaseModel, Generic[T]):
    """Respuesta paginada genérica."""
    total: int
    skip: int
    limit: int
    items: List[T]


class ErrorResponse(BaseModel):
    """Respuesta de error."""
    detail: str
    error_code: Optional[str] = None


class SuccessResponse(BaseModel):
    """Respuesta exitosa."""
    message: str
    data: Optional[Any] = None


class StatusResponse(BaseModel):
    """Respuesta de estado."""
    status: str
    message: Optional[str] = None
    timestamp: datetime = datetime.now()


class HealthCheckResponse(BaseModel):
    """Respuesta de health check."""
    status: str
    version: str
    database: str
    router: str
    timestamp: datetime
