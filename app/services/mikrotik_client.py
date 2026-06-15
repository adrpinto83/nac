"""
Cliente MikroTik REST API para NAC System
Proporciona acceso bidireccional a todos los endpoints del router
"""

import httpx
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class MikroTikClient:
    """
    Cliente REST API para MikroTik
    Maneja toda la comunicación bidireccional con el router
    """

    def __init__(
        self,
        host: str = "192.168.88.1",
        port: int = 8728,
        username: str = "admin",
        password: str = "",
        timeout: int = 10
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.timeout = timeout
        self.base_url = f"http://{host}:{port}"
        self.client = None

    async def __aenter__(self):
        """Context manager entry"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        await self.disconnect()

    async def connect(self):
        """Conectar al router"""
        try:
            auth = (self.username, self.password) if self.password else None
            self.client = httpx.AsyncClient(
                base_url=self.base_url,
                auth=auth,
                verify=False,
                timeout=self.timeout
            )

            # Verificar conexión
            response = await self.client.get("/rest/system/identity")
            if response.status_code == 200:
                logger.info(f"Conectado a MikroTik {self.host}:{self.port}")
                return True
            else:
                logger.error(f"Fallo al conectar: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Error conectando: {e}")
            return False

    async def disconnect(self):
        """Desconectar del router"""
        if self.client:
            await self.client.aclose()
            logger.info("Desconectado del router")

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None
    ) -> Optional[Any]:
        """Realizar request genérico"""
        try:
            url = f"/rest{endpoint}"

            if method == "GET":
                response = await self.client.get(url)
            elif method == "POST":
                response = await self.client.post(url, json=data or {})
            elif method == "PUT":
                response = await self.client.put(url, json=data or {})
            elif method == "DELETE":
                response = await self.client.delete(url)
            else:
                logger.error(f"Método no soportado: {method}")
                return None

            if response.status_code in [200, 201]:
                try:
                    return response.json()
                except:
                    return response.text
            else:
                logger.warning(f"{method} {endpoint} → {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Error en request: {e}")
            return None

    # ============ SISTEMA ============

    async def get_identity(self) -> Optional[Dict]:
        """Obtener información del router"""
        return await self._request("GET", "/system/identity")

    async def get_resource(self) -> Optional[Dict]:
        """Obtener recursos del sistema (CPU, memoria)"""
        return await self._request("GET", "/system/resource")

    async def get_health(self) -> Optional[Dict]:
        """Obtener estado de salud del router"""
        return await self._request("GET", "/system/health")

    # ============ INTERFACES ============

    async def get_interfaces(self) -> List[Dict]:
        """Obtener todas las interfaces"""
        result = await self._request("GET", "/interface")
        return result if isinstance(result, list) else []

    async def get_ethernet_interfaces(self) -> List[Dict]:
        """Obtener solo interfaces ethernet"""
        result = await self._request("GET", "/interface/ethernet")
        return result if isinstance(result, list) else []

    async def get_bridges(self) -> List[Dict]:
        """Obtener bridges"""
        result = await self._request("GET", "/interface/bridge")
        return result if isinstance(result, list) else []

    # ============ IP CONFIGURATION ============

    async def get_addresses(self) -> List[Dict]:
        """Obtener direcciones IP configuradas"""
        result = await self._request("GET", "/ip/address")
        return result if isinstance(result, list) else []

    async def get_routes(self) -> List[Dict]:
        """Obtener tabla de rutas (para monitoreo de failover)"""
        result = await self._request("GET", "/ip/route")
        return result if isinstance(result, list) else []

    # ============ DHCP (MUY IMPORTANTE) ============

    async def get_dhcp_clients(self) -> List[Dict]:
        """Obtener DHCP clients (ISPs)"""
        result = await self._request("GET", "/ip/dhcp-client")
        return result if isinstance(result, list) else []

    async def get_dhcp_servers(self) -> List[Dict]:
        """Obtener DHCP servers"""
        result = await self._request("GET", "/ip/dhcp-server")
        return result if isinstance(result, list) else []

    async def get_dhcp_networks(self) -> List[Dict]:
        """Obtener redes DHCP configuradas"""
        result = await self._request("GET", "/ip/dhcp-server/network")
        return result if isinstance(result, list) else []

    async def get_connected_devices(self) -> List[Dict]:
        """
        🔴 ENDPOINT CRÍTICO
        Obtener dispositivos conectados (DHCP leases)
        Esto es la tabla ARP del router
        """
        result = await self._request("GET", "/ip/dhcp-server/lease")

        if not isinstance(result, list):
            return []

        devices = []
        for lease in result:
            devices.append({
                "id": lease.get(".id"),
                "mac_address": lease.get("mac-address", ""),
                "ip_address": lease.get("address", ""),
                "hostname": lease.get("host-name", "Unknown"),
                "status": lease.get("status", "released"),
                "server": lease.get("server", ""),
                "expires_after": lease.get("expires-after", ""),
                "last_seen": lease.get("last-seen", ""),
                "client_id": lease.get("client-id", "")
            })

        return devices

    # ============ FIREWALL & NAT ============

    async def get_nat_rules(self) -> List[Dict]:
        """Obtener reglas NAT"""
        result = await self._request("GET", "/ip/firewall/nat")
        return result if isinstance(result, list) else []

    async def get_firewall_rules(self) -> List[Dict]:
        """Obtener reglas de firewall"""
        result = await self._request("GET", "/ip/firewall/filter")
        return result if isinstance(result, list) else []

    async def get_address_lists(self) -> List[Dict]:
        """Obtener listas de direcciones (whitelist/blacklist)"""
        result = await self._request("GET", "/ip/firewall/address-list")
        return result if isinstance(result, list) else []

    async def add_to_address_list(
        self,
        list_name: str,
        address: str,
        comment: str = ""
    ) -> bool:
        """Agregar dirección a lista (ej: whitelist)"""
        data = {
            "list": list_name,
            "address": address
        }
        if comment:
            data["comment"] = comment

        result = await self._request("POST", "/ip/firewall/address-list", data)
        return result is not None

    async def remove_from_address_list(self, item_id: str) -> bool:
        """Remover dirección de lista"""
        result = await self._request("DELETE", f"/ip/firewall/address-list/{item_id}")
        return result is not None

    # ============ QoS (QUALITY OF SERVICE) ============

    async def get_queues(self) -> List[Dict]:
        """Obtener colas simples (límites de ancho de banda)"""
        result = await self._request("GET", "/queue/simple")
        return result if isinstance(result, list) else []

    async def create_queue(
        self,
        target_ip: str,
        max_limit_down: str,
        max_limit_up: str,
        priority: int = 8
    ) -> Optional[str]:
        """Crear límite de ancho de banda"""
        data = {
            "target": target_ip,
            "max-limit": f"{max_limit_down}/{max_limit_up}",
            "priority": priority
        }
        result = await self._request("POST", "/queue/simple", data)

        if isinstance(result, dict) and ".id" in result:
            return result[".id"]
        return None

    async def delete_queue(self, queue_id: str) -> bool:
        """Eliminar límite de ancho de banda"""
        result = await self._request("DELETE", f"/queue/simple/{queue_id}")
        return result is not None

    # ============ DNS ============

    async def get_dns_config(self) -> Optional[Dict]:
        """Obtener configuración DNS"""
        return await self._request("GET", "/ip/dns")

    async def get_dns_static(self) -> List[Dict]:
        """Obtener registros DNS estáticos"""
        result = await self._request("GET", "/ip/dns/static")
        return result if isinstance(result, list) else []

    # ============ ÚTILES PARA MONITOREO ============

    async def get_isp_status(self) -> Dict[str, Dict]:
        """
        🔴 ENDPOINT CRÍTICO
        Obtener estado de ISPs y conexiones WAN
        Importante para monitoreo de failover
        """
        clients = await self.get_dhcp_clients()

        isp_status = {}
        for client in clients:
            interface = client.get("interface", "unknown")
            status = client.get("status", "down")
            address = client.get("address", "No IP")
            gateway = client.get("server", "N/A")

            isp_status[interface] = {
                "online": status == "bound",
                "status": status,
                "ip_address": address,
                "gateway": gateway,
                "interface": interface
            }

        return isp_status

    async def check_internet_connectivity(self) -> bool:
        """Verificar si hay conectividad a Internet (checkear rutas)"""
        routes = await self.get_routes()

        # Hay rutas por defecto (0.0.0.0/0)
        for route in routes:
            if route.get("dst-address") == "0.0.0.0/0":
                return True

        return False

    async def get_summary(self) -> Dict[str, Any]:
        """
        Obtener resumen completo del router para dashboard
        """
        identity = await self.get_identity()
        resource = await self.get_resource()
        devices = await self.get_connected_devices()
        isp_status = await self.get_isp_status()
        internet = await self.check_internet_connectivity()

        return {
            "identity": identity,
            "resource": resource,
            "connected_devices": len(devices),
            "devices": devices,
            "isp_status": isp_status,
            "internet_online": internet,
            "timestamp": datetime.now().isoformat()
        }
