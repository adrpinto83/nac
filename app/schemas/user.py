"""Esquemas Pydantic para usuarios."""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    """Crear usuario."""
    username: str = Field(..., min_length=3, max_length=50)
    full_name: str = Field(..., min_length=1, max_length=100)
    cedula: Optional[str] = None
    cargo: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    password: str = Field(..., min_length=6)


class UserUpdate(BaseModel):
    """Actualizar usuario."""
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    cargo: Optional[str] = None
    status: Optional[str] = None


class UserResponse(BaseModel):
    """Respuesta usuario."""
    id: int
    username: str
    full_name: str
    cedula: Optional[str]
    cargo: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    role: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class OperatorCreate(BaseModel):
    """Crear operador."""
    username: str = Field(..., min_length=3)
    password: str = Field(..., min_length=6)
    role: str = Field(..., pattern="^(SUPERADMIN|ADMIN_RED|SOPORTE)$")


class OperatorResponse(BaseModel):
    """Respuesta operador."""
    id: int
    username: str
    role: str
    active: bool
    created_at: datetime
    last_login: Optional[datetime]

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    """Request de login."""
    username: str
    password: str


class TokenResponse(BaseModel):
    """Respuesta con token JWT."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
