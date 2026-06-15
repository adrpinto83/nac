"""
Data classes para respuestas del router RouterOS.
"""

from dataclasses import dataclass
from typing import Optional, List


@dataclass
class RouterIdentity:
    """Identidad del router."""
    name: str
    platform: Optional[str] = None


@dataclass
class ARPEntry:
    """Entrada de tabla ARP."""
    mac_address: str
    address: str
    interface: str
    disabled: bool = False
    dynamic: bool = True


@dataclass
class DHCPLease:
    """Lease DHCP."""
    mac_address: str
    address: str
    server: str = "dhcp-server"
    disabled: bool = False
    comment: Optional[str] = None


@dataclass
class WifiRegistration:
    """Registro de cliente WiFi."""
    mac_address: str
    interface: str
    signal_strength: int
    rx_rate: int
    tx_rate: int
    uptime: str


@dataclass
class SimpleQueue:
    """Simple Queue (cola QoS)."""
    id: str
    name: str
    target: str
    max_limit: Optional[str] = None
    priority: int = 3
    disabled: bool = False
    bytes_in: int = 0
    bytes_out: int = 0
    packets_in: int = 0
    packets_out: int = 0
    comment: Optional[str] = None


@dataclass
class AddressListEntry:
    """Entrada en address list."""
    id: str
    list: str
    address: str
    disabled: bool = False
    comment: Optional[str] = None
    timeout: Optional[str] = None


@dataclass
class DNSStaticEntry:
    """Entrada DNS estática."""
    id: str
    name: str
    address: str
    disabled: bool = False
    comment: Optional[str] = None


@dataclass
class HotspotActive:
    """Sesión activa en hotspot."""
    user: str
    address: str
    mac_address: str
    uptime: str
    session_time_left: Optional[str] = None


@dataclass
class Interface:
    """Información de interfaz."""
    name: str
    type: str
    disabled: bool = False
    running: bool = True
    rx_byte: int = 0
    tx_byte: int = 0
    rx_packet: int = 0
    tx_packet: int = 0


@dataclass
class RouterStatus:
    """Estado general del router."""
    name: str
    uptime: str
    version: str
    cpu_load: Optional[float] = None
    memory_used: Optional[int] = None
    memory_total: Optional[int] = None


@dataclass
class HealthCheckResult:
    """Resultado de health check."""
    status: str  # "ok" o "error"
    latency_ms: float
    timestamp: str
    message: Optional[str] = None
