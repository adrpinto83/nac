"""Servicio de dispositivos (BD + RouterOS)."""

from typing import Optional, List
from app.models import Database, DeviceModel, AuditLogModel
from routeros.client import RouterOSClient


class DeviceService:
    """Servicio de dispositivos con integración RouterOS."""

    def __init__(self, db: Database, router: RouterOSClient):
        self.db = db
        self.router = router
        self.device_model = DeviceModel(db)
        self.audit_model = AuditLogModel(db)

    async def register_device_on_router(
        self,
        mac_address: str,
        device_name: str,
        profile_id: Optional[int] = None,
    ) -> Optional[dict]:
        """Registra dispositivo: BD + Whitelist + Queue en router."""
        try:
            # Agregar a whitelist en router
            entry_id = await self.router.add_to_address_list(
                list_name="mac-whitelist",
                address=mac_address,
                comment=device_name,
            )

            # Crear queue QoS si hay perfil
            queue_id = None
            if profile_id:
                queue_id = await self.router.create_queue(
                    name=f"{device_name}-queue",
                    target=f"192.168.88.0/24",  # Default
                    max_limit="5M/2M",
                )

            return {
                "mac_address": mac_address,
                "router_entry_id": entry_id,
                "router_queue_id": queue_id,
            }
        except Exception as e:
            print(f"Error registrando en router: {e}")
            return None

    async def unregister_device_from_router(self, mac_address: str) -> bool:
        """Desregistra dispositivo: elimina de whitelist y queue en router."""
        try:
            # Obtener entradas de whitelist
            entries = await self.router.get_address_lists()
            for entry in entries:
                if entry.address == mac_address and entry.list == "mac-whitelist":
                    await self.router.remove_from_address_list(entry.id)

            # Obtener queues
            queues = await self.router.get_simple_queues()
            for queue in queues:
                if mac_address in queue.name:
                    await self.router.delete_queue(queue.id)

            return True
        except Exception as e:
            print(f"Error desregistrando: {e}")
            return False

    async def block_device_on_router(self, mac_address: str) -> bool:
        """Bloquea dispositivo en router (desactiva whitelist)."""
        try:
            entries = await self.router.get_address_lists()
            for entry in entries:
                if entry.address == mac_address and entry.list == "mac-whitelist":
                    await self.router.update_address_list_entry(entry.id, disabled=True)
            return True
        except Exception as e:
            print(f"Error bloqueando: {e}")
            return False

    async def unblock_device_on_router(self, mac_address: str) -> bool:
        """Desbloquea dispositivo en router (activa whitelist)."""
        try:
            entries = await self.router.get_address_lists()
            for entry in entries:
                if entry.address == mac_address and entry.list == "mac-whitelist":
                    await self.router.update_address_list_entry(entry.id, disabled=False)
            return True
        except Exception as e:
            print(f"Error desbloqueando: {e}")
            return False

    async def get_live_devices(self) -> List[dict]:
        """Obtiene dispositivos vivos en la red (ARP)."""
        try:
            arp_table = await self.router.get_arp_table()
            registered_macs = await self.device_model.get_registered_macs()

            devices = []
            for entry in arp_table:
                devices.append({
                    "mac_address": entry.mac_address,
                    "ip_address": entry.address,
                    "interface": entry.interface,
                    "is_registered": entry.mac_address in registered_macs,
                })

            return devices
        except Exception as e:
            print(f"Error obteniendo ARP: {e}")
            return []

    async def sync_queue_limits(self, device_id: int, max_limit: str) -> bool:
        """Sincroniza límites de QoS en router."""
        try:
            device = await self.device_model.get_device_by_id(device_id)
            if not device:
                return False

            queues = await self.router.get_simple_queues()
            for queue in queues:
                if device["mac_address"] in queue.name:
                    await self.router.update_queue(queue.id, max_limit=max_limit)
                    return True

            return False
        except Exception as e:
            print(f"Error sincronizando QoS: {e}")
            return False
