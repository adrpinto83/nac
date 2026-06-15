"""Esquemas Pydantic para dashboard."""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class DeviceStats(BaseModel):
    """Estadísticas de dispositivo."""
    mac_address: str
    device_name: str
    status: str
    bytes_in: int
    bytes_out: int
    active: bool


class DashboardMetrics(BaseModel):
    """Métricas del dashboard."""
    total_registered_devices: int
    active_devices_now: int
    suspended_devices: int
    expired_devices: int
    unregistered_macs: int
    router_latency_ms: float
    router_status: str
    timestamp: datetime


class TopDevicesByTraffic(BaseModel):
    """Top dispositivos por tráfico."""
    mac_address: str
    device_name: str
    full_name: Optional[str]
    bytes_in: int
    bytes_out: int
    total_bytes: int


class Alert(BaseModel):
    """Alerta del sistema."""
    level: str  # "info", "warning", "error"
    message: str
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    timestamp: datetime


class UnregisteredMAC(BaseModel):
    """MAC no registrada."""
    mac_address: str
    ip_address: Optional[str]
    interface: str
    first_seen: datetime
    last_seen: datetime
