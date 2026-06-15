"""
routeros_client.py — Cliente REST API para MikroTik RouterOS
Maneja: firewall rules, address-lists, simple queues, DNS entries, ARP
"""

import httpx
import asyncio
from typing import List, Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)

class RouterOSClient:
    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 443,
        username: str = "api-container",
        password: str = "NAC_MikroTik_2025",
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.base_url = f"https://{host}:{port}/rest"
        self.client = None

    async def connect(self):
        """Crear cliente HTTP con autenticación"""
        self.client = httpx.AsyncClient(
            auth=(self.username, self.password),
            verify=False,  # Certificado autofirmado
            timeout=10.0,
        )
        logger.info(f"Conectado a RouterOS en {self.host}:{self.port}")

    async def disconnect(self):
        """Cerrar conexión"""
        if self.client:
            await self.client.aclose()

    async def _request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict] = None,
        retry: int = 3,
    ) -> Dict:
        """Realizar request con reintento automático"""
        if not self.client:
            await self.connect()

        url = f"{self.base_url}{endpoint}"

        for attempt in range(retry):
            try:
                if method == "GET":
                    response = await self.client.get(url)
                elif method == "POST":
                    response = await self.client.post(url, json=json_data)
                elif method == "PUT":
                    response = await self.client.put(url, json=json_data)
                elif method == "DELETE":
                    response = await self.client.delete(url)
                else:
                    raise ValueError(f"Method {method} not supported")

                if response.status_code in [200, 201]:
                    return response.json() if response.text else {}

                elif response.status_code == 404:
                    logger.warning(f"Endpoint no encontrado: {url}")
                    return {}

                elif response.status_code in [401, 403]:
                    logger.error("Autenticación fallida con RouterOS")
                    raise Exception("RouterOS authentication failed")

                else:
                    logger.warning(
                        f"RouterOS error ({response.status_code}): {response.text}"
                    )

            except (httpx.ConnectError, httpx.TimeoutException, Exception) as e:
                logger.warning(
                    f"Attempt {attempt + 1}/{retry} failed: {e}. "
                    f"Retrying in {2 ** attempt}s..."
                )
                if attempt < retry - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    raise

        raise Exception(f"Failed to reach RouterOS after {retry} attempts")

    # ============ FIREWALL ADDRESS-LIST ============

    async def add_mac_to_whitelist(self, mac: str, comment: str = "") -> bool:
        """Agregar MAC a lista whitelist"""
        try:
            result = await self._request(
                "POST",
                "/ip/firewall/address-list",
                {
                    "list": "mac-whitelist",
                    "address": mac,
                    "comment": comment or f"User: {mac}",
                },
            )
            logger.info(f"MAC {mac} agregada a whitelist")
            return True
        except Exception as e:
            logger.error(f"Error agregando {mac} a whitelist: {e}")
            return False

    async def remove_mac_from_whitelist(self, mac: str) -> bool:
        """Eliminar MAC de lista whitelist"""
        try:
            # Buscar el ID de la entrada
            entries = await self._request("GET", "/ip/firewall/address-list")
            for entry in entries:
                if entry.get("address") == mac and entry.get("list") == "mac-whitelist":
                    entry_id = entry.get(".id")
                    await self._request("DELETE", f"/ip/firewall/address-list/{entry_id}")
                    logger.info(f"MAC {mac} removida de whitelist")
                    return True
            return False
        except Exception as e:
            logger.error(f"Error removiendo {mac} de whitelist: {e}")
            return False

    async def add_mac_to_blocklist(self, mac: str, comment: str = "") -> bool:
        """Agregar MAC a lista de bloqueo"""
        try:
            result = await self._request(
                "POST",
                "/ip/firewall/address-list",
                {
                    "list": "mac-blocked",
                    "address": mac,
                    "comment": comment or f"Blocked: {mac}",
                },
            )
            logger.info(f"MAC {mac} agregada a blocklist")
            return True
        except Exception as e:
            logger.error(f"Error agregando {mac} a blocklist: {e}")
            return False

    async def remove_mac_from_blocklist(self, mac: str) -> bool:
        """Eliminar MAC de lista de bloqueo"""
        try:
            entries = await self._request("GET", "/ip/firewall/address-list")
            for entry in entries:
                if entry.get("address") == mac and entry.get("list") == "mac-blocked":
                    entry_id = entry.get(".id")
                    await self._request("DELETE", f"/ip/firewall/address-list/{entry_id}")
                    logger.info(f"MAC {mac} removida de blocklist")
                    return True
            return False
        except Exception as e:
            logger.error(f"Error removiendo {mac} de blocklist: {e}")
            return False

    # ============ SIMPLE QUEUE (QoS) ============

    async def create_queue(
        self,
        queue_name: str,
        target_ip: str,
        max_limit: str,
        priority: int = 3,
    ) -> bool:
        """Crear Simple Queue para QoS de un usuario"""
        try:
            result = await self._request(
                "POST",
                "/queue/simple",
                {
                    "name": queue_name,
                    "target": target_ip,
                    "max-limit": max_limit,
                    "priority": priority,
                },
            )
            logger.info(f"Queue {queue_name} creada para {target_ip}")
            return True
        except Exception as e:
            logger.error(f"Error creando queue {queue_name}: {e}")
            return False

    async def update_queue(
        self,
        queue_name: str,
        max_limit: str,
        priority: int = 3,
    ) -> bool:
        """Actualizar Simple Queue existente"""
        try:
            queues = await self._request("GET", "/queue/simple")
            for queue in queues:
                if queue.get("name") == queue_name:
                    queue_id = queue.get(".id")
                    await self._request(
                        "PUT",
                        f"/queue/simple/{queue_id}",
                        {
                            "max-limit": max_limit,
                            "priority": priority,
                        },
                    )
                    logger.info(f"Queue {queue_name} actualizada")
                    return True
            return False
        except Exception as e:
            logger.error(f"Error actualizando queue {queue_name}: {e}")
            return False

    async def delete_queue(self, queue_name: str) -> bool:
        """Eliminar Simple Queue"""
        try:
            queues = await self._request("GET", "/queue/simple")
            for queue in queues:
                if queue.get("name") == queue_name:
                    queue_id = queue.get(".id")
                    await self._request("DELETE", f"/queue/simple/{queue_id}")
                    logger.info(f"Queue {queue_name} eliminada")
                    return True
            return False
        except Exception as e:
            logger.error(f"Error eliminando queue {queue_name}: {e}")
            return False

    async def get_queue_stats(self, queue_name: str) -> Dict:
        """Obtener estadísticas de una queue"""
        try:
            queues = await self._request("GET", "/queue/simple")
            for queue in queues:
                if queue.get("name") == queue_name:
                    return {
                        "bytes_in": int(queue.get("bytes", 0)),
                        "packets": int(queue.get("packets", 0)),
                    }
            return {}
        except Exception as e:
            logger.error(f"Error obteniendo stats de {queue_name}: {e}")
            return {}

    # ============ DNS ESTÁTICA ============

    async def add_dns_entry(
        self,
        domain: str,
        address: str = "0.0.0.0",
        comment: str = "",
    ) -> bool:
        """Crear entrada DNS estática (bloqueo)"""
        try:
            result = await self._request(
                "POST",
                "/ip/dns/static",
                {
                    "name": domain,
                    "address": address,
                    "comment": comment or f"Blocked: {domain}",
                },
            )
            logger.info(f"DNS entry {domain} agregada")
            return True
        except Exception as e:
            logger.error(f"Error agregando DNS {domain}: {e}")
            return False

    async def remove_dns_entry(self, domain: str) -> bool:
        """Eliminar entrada DNS estática"""
        try:
            entries = await self._request("GET", "/ip/dns/static")
            for entry in entries:
                if entry.get("name") == domain:
                    entry_id = entry.get(".id")
                    await self._request("DELETE", f"/ip/dns/static/{entry_id}")
                    logger.info(f"DNS entry {domain} eliminada")
                    return True
            return False
        except Exception as e:
            logger.error(f"Error eliminando DNS {domain}: {e}")
            return False

    # ============ ARP / HOST DETECTION ============

    async def get_arp_table(self) -> List[Dict]:
        """Obtener tabla ARP para detectar dispositivos activos"""
        try:
            arp_entries = await self._request("GET", "/ip/arp")
            return [
                {
                    "mac": entry.get("mac-address"),
                    "ip": entry.get("address"),
                    "interface": entry.get("interface"),
                }
                for entry in arp_entries
                if entry.get("mac-address")
            ]
        except Exception as e:
            logger.error(f"Error leyendo ARP: {e}")
            return []

    async def find_mac_by_ip(self, ip: str) -> Optional[str]:
        """Buscar MAC address por IP en tabla ARP"""
        try:
            arp_entries = await self.get_arp_table()
            for entry in arp_entries:
                if entry.get("ip") == ip:
                    return entry.get("mac")
            return None
        except Exception as e:
            logger.error(f"Error buscando MAC para IP {ip}: {e}")
            return None

    # ============ HOTSPOT / ACTIVE USERS ============

    async def get_active_users(self) -> List[Dict]:
        """Obtener usuarios activos en hotspot"""
        try:
            active = await self._request("GET", "/ip/hotspot/active")
            return [
                {
                    "user": entry.get("user"),
                    "ip": entry.get("address"),
                    "mac": entry.get("mac-address"),
                    "uptime": entry.get("uptime"),
                }
                for entry in active
            ]
        except Exception as e:
            logger.error(f"Error obteniendo usuarios activos: {e}")
            return []

    # ============ DHCP LEASE ============

    async def create_dhcp_lease(
        self,
        mac: str,
        ip: str,
        comment: str = "",
    ) -> bool:
        """Crear binding DHCP (MAC → IP fija)"""
        try:
            result = await self._request(
                "POST",
                "/ip/dhcp-server/lease",
                {
                    "mac-address": mac,
                    "address": ip,
                    "server": "bridge-lan",
                    "comment": comment or f"User: {mac}",
                },
            )
            logger.info(f"DHCP lease {mac} → {ip} creado")
            return True
        except Exception as e:
            logger.error(f"Error creando DHCP lease: {e}")
            return False

    async def delete_dhcp_lease(self, mac: str) -> bool:
        """Eliminar binding DHCP"""
        try:
            leases = await self._request("GET", "/ip/dhcp-server/lease")
            for lease in leases:
                if lease.get("mac-address") == mac:
                    lease_id = lease.get(".id")
                    await self._request("DELETE", f"/ip/dhcp-server/lease/{lease_id}")
                    logger.info(f"DHCP lease {mac} eliminado")
                    return True
            return False
        except Exception as e:
            logger.error(f"Error eliminando DHCP lease {mac}: {e}")
            return False

    # ============ UTILITY ============

    async def get_interface_stats(self, interface: str) -> Dict:
        """Obtener estadísticas de una interfaz"""
        try:
            interfaces = await self._request("GET", "/interface")
            for iface in interfaces:
                if iface.get("name") == interface:
                    return {
                        "bytes_in": int(iface.get("rx-byte", 0)),
                        "bytes_out": int(iface.get("tx-byte", 0)),
                        "packets_in": int(iface.get("rx-packet", 0)),
                        "packets_out": int(iface.get("tx-packet", 0)),
                    }
            return {}
        except Exception as e:
            logger.error(f"Error obteniendo stats de {interface}: {e}")
            return {}

    async def test_connection(self) -> bool:
        """Test de conectividad"""
        try:
            if not self.client:
                await self.connect()
            await self._request("GET", "/system/identity")
            return True
        except Exception:
            return False
