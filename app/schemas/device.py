"""Esquemas Pydantic para dispositivos."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class DeviceCreate(BaseModel):
    """Crear dispositivo."""
    mac_address: str = Field(..., pattern=r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$")
    device_name: str = Field(..., min_length=1, max_length=100)
    device_type: Optional[str] = None
    user_id: int
    profile_id: Optional[int] = None
    comment: Optional[str] = None


class DeviceUpdate(BaseModel):
    """Actualizar dispositivo."""
    device_name: Optional[str] = None
    device_type: Optional[str] = None
    profile_id: Optional[int] = None
    status: Optional[str] = None
    expires_at: Optional[str] = None
    comment: Optional[str] = None


class DeviceResponse(BaseModel):
    """Respuesta dispositivo."""
    id: int
    mac_address: str
    device_name: str
    device_type: Optional[str]
    user_id: Optional[int]
    profile_id: Optional[int]
    assigned_ip: Optional[str]
    status: str
    last_seen: Optional[datetime]
    expires_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class DeviceWithUserResponse(DeviceResponse):
    """Respuesta dispositivo con información de usuario."""
    full_name: Optional[str] = None
    cedula: Optional[str] = None
    email: Optional[str] = None
    profile_name: Optional[str] = None


class ARPDevice(BaseModel):
    """Dispositivo visible en ARP."""
    mac_address: str
    ip_address: str
    interface: str
    is_registered: bool = False


class LiveDevicesResponse(BaseModel):
    """Respuesta de dispositivos vivos en la red."""
    total: int
    registered: int
    unregistered: int
    devices: list[ARPDevice]
