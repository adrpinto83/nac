"""
Cliente REST async para MikroTik RouterOS.

Comunicación con router vía API REST con autenticación HTTP Basic.
Soporta todos los endpoints necesarios para el sistema NAC.
"""

import asyncio
import logging
import time
from typing import List, Optional, Dict, Any
from datetime import datetime

import httpx

from .auth import BasicAuth
from .exceptions import (
    RouterOSConnectionError,
    RouterOSAuthError,
    RouterOSNotFoundError,
    RouterOSValidationError,
    RouterOSServerError,
    RouterOSTimeoutError,
    RouterOSInvalidResponseError,
)
from .models import (
    RouterIdentity,
    ARPEntry,
    DHCPLease,
    SimpleQueue,
    AddressListEntry,
    DNSStaticEntry,
    HotspotActive,
    Interface,
    RouterStatus,
    HealthCheckResult,
)


logger = logging.getLogger(__name__)


class RouterOSClient:
    """
    Cliente async para RouterOS REST API.

    Proporciona métodos para todas las operaciones necesarias:
    - Lectura de estado (ARP, DHCP, hotspot)
    - Gestión de access control (address-lists)
    - Gestión de QoS (simple queues)
    - Gestión de DNS (entradas estáticas)
    - Health checks
    """

    def __init__(
        self,
        host: str = "192.168.88.1",
        port: int = 80,
        username: str = "api-container",
        password: str = "NAC_MikroTik_2025",
        timeout: float = 10.0,
        verify_ssl: bool = False,
        max_retries: int = 3,
    ):
        """
        Inicializa cliente RouterOS.

        Args:
            host: IP del router
            port: Puerto REST API
            username: Usuario API
            password: Contraseña
            timeout: Timeout en segundos
            verify_ssl: Verificar certificado SSL
            max_retries: Reintentos máximos
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.max_retries = max_retries
        self.base_url = f"http://{host}:{port}/rest"
        self.auth = BasicAuth(username, password)
        self.client: Optional[httpx.AsyncClient] = None
        self.connected = False

    async def connect(self) -> None:
        """Abre conexión al router."""
        try:
            self.client = httpx.AsyncClient(
                auth=httpx.BasicAuth(self.username, self.password),
                verify=self.verify_ssl,
                timeout=self.timeout,
            )
            # Verificar conectividad
            await self.health_check()
            self.connected = True
            logger.info(f"Conectado a RouterOS en {self.host}:{self.port}")
        except Exception as e:
            self.connected = False
            raise RouterOSConnectionError(self.host, self.port, str(e))

    async def disconnect(self) -> None:
        """Cierra conexión al router."""
        if self.client:
            await self.client.aclose()
            self.connected = False
            logger.info("Desconectado de RouterOS")

    async def _request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Realiza request HTTP con retry automático.

        Args:
            method: GET, POST, PATCH, DELETE
            endpoint: Ruta relativa (ej: /ip/arp)
            json_data: Datos JSON (para POST/PATCH)

        Returns:
            Respuesta JSON

        Raises:
            RouterOSAuthError: Credenciales inválidas (401)
            RouterOSNotFoundError: Endpoint no existe (404)
            RouterOSValidationError: Datos inválidos (422)
            RouterOSServerError: Error servidor (500)
            RouterOSTimeoutError: Timeout
        """
        if not self.client:
            await self.connect()

        url = f"{self.base_url}{endpoint}"

        for attempt in range(self.max_retries):
            try:
                start_time = time.time()

                if method == "GET":
                    response = await self.client.get(url)
                elif method == "POST":
                    response = await self.client.post(url, json=json_data)
                elif method == "PATCH":
                    response = await self.client.patch(url, json=json_data)
                elif method == "DELETE":
                    response = await self.client.delete(url)
                else:
                    raise ValueError(f"Método {method} no soportado")

                latency = time.time() - start_time
                logger.debug(f"{method} {endpoint} - {response.status_code} ({latency:.2f}s)")

                # Manejo de códigos de estado
                if response.status_code in [200, 201]:
                    try:
                        return response.json() if response.text else {}
                    except ValueError:
                        return {}

                elif response.status_code == 401:
                    raise RouterOSAuthError(self.username)

                elif response.status_code == 404:
                    raise RouterOSNotFoundError(endpoint)

                elif response.status_code == 422:
                    try:
                        error_data = response.json()
                    except ValueError:
                        error_data = {"message": response.text}
                    raise RouterOSValidationError(endpoint, error_data)

                elif response.status_code >= 500:
                    raise RouterOSServerError(response.status_code, response.text)

                else:
                    logger.warning(f"Código HTTP inesperado: {response.status_code}")
                    return {}

            except asyncio.TimeoutError:
                raise RouterOSTimeoutError(self.timeout)

            except (httpx.ConnectError, httpx.TimeoutException) as e:
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(
                        f"Intento {attempt + 1}/{self.max_retries} falló: {e}. "
                        f"Reintentando en {wait_time}s..."
                    )
                    await asyncio.sleep(wait_time)
                else:
                    raise RouterOSConnectionError(self.host, self.port, str(e))

            except (
                RouterOSAuthError,
                RouterOSNotFoundError,
                RouterOSValidationError,
                RouterOSServerError,
            ):
                raise

        raise RouterOSConnectionError(
            self.host, self.port, f"Falló después de {self.max_retries} intentos"
        )

    # ========== LECTURA DE ESTADO ==========

    async def get_router_identity(self) -> RouterIdentity:
        """Obtiene identidad del router."""
        data = await self._request("GET", "/system/identity")
        return RouterIdentity(
            name=data.get("name", "MikroTik"),
            platform=data.get("platform"),
        )

    async def get_arp_table(self) -> List[ARPEntry]:
        """Obtiene tabla ARP (dispositivos en red)."""
        data = await self._request("GET", "/ip/arp")
        entries = []
        for item in data:
            if item.get("mac-address"):
                entries.append(
                    ARPEntry(
                        mac_address=item.get("mac-address", ""),
                        address=item.get("address", ""),
                        interface=item.get("interface", ""),
                        disabled=item.get("disabled", False),
                        dynamic=item.get("dynamic", True),
                    )
                )
        return entries

    async def get_dhcp_leases(self) -> List[DHCPLease]:
        """Obtiene leases DHCP activos."""
        data = await self._request("GET", "/ip/dhcp-server/lease")
        leases = []
        for item in data:
            leases.append(
                DHCPLease(
                    mac_address=item.get("mac-address", ""),
                    address=item.get("address", ""),
                    server=item.get("server", ""),
                    disabled=item.get("disabled", False),
                    comment=item.get("comment"),
                )
            )
        return leases

    async def get_hotspot_active(self) -> List[HotspotActive]:
        """Obtiene sesiones activas de hotspot."""
        data = await self._request("GET", "/ip/hotspot/active")
        sessions = []
        for item in data:
            # bytes-in / bytes-out vienen como int o string desde RouterOS
            try:
                b_in = int(item.get("bytes-in", 0) or 0)
            except (ValueError, TypeError):
                b_in = 0
            try:
                b_out = int(item.get("bytes-out", 0) or 0)
            except (ValueError, TypeError):
                b_out = 0
            sessions.append(
                HotspotActive(
                    user=item.get("user", ""),
                    address=item.get("address", ""),
                    mac_address=item.get("mac-address", ""),
                    uptime=item.get("uptime", ""),
                    session_time_left=item.get("session-time-left"),
                    bytes_in=b_in,
                    bytes_out=b_out,
                )
            )
        return sessions

    async def get_interfaces(self) -> List[Interface]:
        """Obtiene información de interfaces."""
        data = await self._request("GET", "/interface")
        interfaces = []
        for item in data:
            interfaces.append(
                Interface(
                    name=item.get("name", ""),
                    type=item.get("type", ""),
                    disabled=item.get("disabled", False),
                    running=item.get("running", True),
                    rx_byte=int(item.get("rx-byte", 0)),
                    tx_byte=int(item.get("tx-byte", 0)),
                    rx_packet=int(item.get("rx-packet", 0)),
                    tx_packet=int(item.get("tx-packet", 0)),
                )
            )
        return interfaces

    # ========== ADDRESS LISTS (WHITELIST/BLOCKLIST) ==========

    async def get_address_lists(self) -> List[AddressListEntry]:
        """Obtiene todas las entradas de address-list."""
        data = await self._request("GET", "/ip/firewall/address-list")
        entries = []
        for item in data:
            entries.append(
                AddressListEntry(
                    id=item.get(".id", ""),
                    list=item.get("list", ""),
                    address=item.get("address", ""),
                    disabled=item.get("disabled", False),
                    comment=item.get("comment"),
                    timeout=item.get("timeout"),
                )
            )
        return entries

    async def add_to_address_list(
        self, list_name: str, address: str, comment: str = "", timeout: Optional[str] = None
    ) -> str:
        """
        Agrega entrada a address-list.

        Args:
            list_name: Nombre de lista (ej: mac-whitelist)
            address: MAC o IP a agregar
            comment: Comentario
            timeout: Timeout (ej: "00:10:00")

        Returns:
            ID de entrada creada
        """
        data = {
            "list": list_name,
            "address": address,
            "comment": comment,
        }
        if timeout:
            data["timeout"] = timeout

        response = await self._request("POST", "/ip/firewall/address-list", json_data=data)
        return response.get(".id", "")

    async def remove_from_address_list(self, entry_id: str) -> bool:
        """Elimina entrada de address-list."""
        await self._request("DELETE", f"/ip/firewall/address-list/{entry_id}")
        return True

    async def update_address_list_entry(
        self, entry_id: str, disabled: Optional[bool] = None, comment: Optional[str] = None
    ) -> bool:
        """Actualiza entrada de address-list."""
        data = {}
        if disabled is not None:
            data["disabled"] = disabled
        if comment is not None:
            data["comment"] = comment

        if data:
            await self._request("PATCH", f"/ip/firewall/address-list/{entry_id}", json_data=data)
        return True

    # ========== SIMPLE QUEUES (QoS) ==========

    async def get_simple_queues(self) -> List[SimpleQueue]:
        """Obtiene todas las simple queues."""
        data = await self._request("GET", "/queue/simple")
        queues = []
        for item in data:
            queues.append(
                SimpleQueue(
                    id=item.get(".id", ""),
                    name=item.get("name", ""),
                    target=item.get("target", ""),
                    max_limit=item.get("max-limit"),
                    priority=int(item.get("priority", 3)),
                    disabled=item.get("disabled", False),
                    bytes_in=int(item.get("bytes", 0)),
                    bytes_out=int(item.get("bytes", 0)),
                    packets_in=int(item.get("packets", 0)),
                    packets_out=int(item.get("packets", 0)),
                    comment=item.get("comment"),
                )
            )
        return queues

    async def create_queue(
        self,
        name: str,
        target: str,
        max_limit: str,
        priority: int = 3,
        comment: str = "",
    ) -> str:
        """
        Crea nueva simple queue.

        Args:
            name: Nombre de la cola
            target: IP de destino (ej: 192.168.88.100/32)
            max_limit: Límite (ej: "5M/2M")
            priority: Prioridad (1-8)
            comment: Comentario

        Returns:
            ID de cola creada
        """
        data = {
            "name": name,
            "target": target,
            "max-limit": max_limit,
            "priority": priority,
        }
        if comment:
            data["comment"] = comment

        response = await self._request("POST", "/queue/simple", json_data=data)
        return response.get(".id", "")

    async def delete_queue(self, queue_id: str) -> bool:
        """Elimina simple queue."""
        await self._request("DELETE", f"/queue/simple/{queue_id}")
        return True

    async def update_queue(
        self,
        queue_id: str,
        max_limit: Optional[str] = None,
        priority: Optional[int] = None,
        disabled: Optional[bool] = None,
    ) -> bool:
        """Actualiza simple queue."""
        data = {}
        if max_limit is not None:
            data["max-limit"] = max_limit
        if priority is not None:
            data["priority"] = priority
        if disabled is not None:
            data["disabled"] = disabled

        if data:
            await self._request("PATCH", f"/queue/simple/{queue_id}", json_data=data)
        return True

    # ========== DNS ESTÁTICAS ==========

    async def get_dns_static(self) -> List[DNSStaticEntry]:
        """Obtiene todas las entradas DNS estáticas."""
        data = await self._request("GET", "/ip/dns/static")
        entries = []
        for item in data:
            entries.append(
                DNSStaticEntry(
                    id=item.get(".id", ""),
                    name=item.get("name", ""),
                    address=item.get("address", ""),
                    disabled=item.get("disabled", False),
                    comment=item.get("comment"),
                )
            )
        return entries

    async def add_dns_entry(
        self, domain: str, address: str = "0.0.0.0", comment: str = ""
    ) -> str:
        """
        Agrega entrada DNS estática.

        Args:
            domain: Dominio a bloquear
            address: IP de redirección (default: 0.0.0.0)
            comment: Comentario

        Returns:
            ID de entrada creada
        """
        data = {
            "name": domain,
            "address": address,
        }
        if comment:
            data["comment"] = comment

        response = await self._request("POST", "/ip/dns/static", json_data=data)
        return response.get(".id", "")

    async def delete_dns_entry(self, entry_id: str) -> bool:
        """Elimina entrada DNS estática."""
        await self._request("DELETE", f"/ip/dns/static/{entry_id}")
        return True

    # ========== HEALTH CHECK ==========

    async def health_check(self) -> HealthCheckResult:
        """
        Realiza health check del router.

        Returns:
            Resultado del health check
        """
        try:
            start_time = time.time()
            identity = await self.get_router_identity()
            latency = (time.time() - start_time) * 1000  # Convertir a ms

            return HealthCheckResult(
                status="ok",
                latency_ms=latency,
                timestamp=datetime.now().isoformat(),
                message=f"Router: {identity.name}",
            )
        except Exception as e:
            return HealthCheckResult(
                status="error",
                latency_ms=0,
                timestamp=datetime.now().isoformat(),
                message=str(e),
            )

    # ========== UTILITY ==========

    async def test_connection(self) -> bool:
        """Simple test de conectividad."""
        try:
            await self.get_router_identity()
            return True
        except Exception:
            return False

    def is_connected(self) -> bool:
        """Retorna estado de conexión."""
        return self.connected and self.client is not None

    async def __aenter__(self):
        """Context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.disconnect()
