"""Esquemas Pydantic para perfiles QoS."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ProfileCreate(BaseModel):
    """Crear perfil QoS."""
    name: str = Field(..., min_length=1, max_length=50)
    max_upload: Optional[str] = Field(None, description="Ej: 10M, 5M, 100k")
    max_download: Optional[str] = Field(None, description="Ej: 10M, 5M, 100k")
    priority: int = Field(3, ge=1, le=8)
    description: Optional[str] = None


class ProfileUpdate(BaseModel):
    """Actualizar perfil QoS."""
    max_upload: Optional[str] = None
    max_download: Optional[str] = None
    priority: Optional[int] = None
    description: Optional[str] = None


class ProfileResponse(BaseModel):
    """Respuesta perfil QoS."""
    id: int
    name: str
    max_upload: Optional[str]
    max_download: Optional[str]
    priority: int
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class DNSCategoryCreate(BaseModel):
    """Crear categoría DNS."""
    name: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None


class DNSCategoryResponse(BaseModel):
    """Respuesta categoría DNS."""
    id: int
    name: str
    description: Optional[str]

    class Config:
        from_attributes = True


class DNSEntryCreate(BaseModel):
    """Crear entrada DNS."""
    domain: str = Field(..., min_length=1)
    category_id: Optional[int] = None
    comment: Optional[str] = None


class DNSEntryResponse(BaseModel):
    """Respuesta entrada DNS."""
    id: int
    domain: str
    category_id: Optional[int]
    address: str
    enabled: bool
    comment: Optional[str]

    class Config:
        from_attributes = True
