"""Servicio de dashboard (métricas en tiempo real)."""

from typing import List, Optional
from datetime import datetime
from app.models import Database, DeviceModel, TrafficModel
from routeros.client import RouterOSClient


class DashboardService:
    """Servicio de dashboard con métricas."""

    def __init__(self, db: Database, router: RouterOSClient):
        self.db = db
        self.router = router
        self.device_model = DeviceModel(db)
        self.traffic_model = TrafficModel(db)

    async def get_metrics(self) -> dict:
        """Obtiene métricas del dashboard."""
        # Contar dispositivos
        total_registered = await self.device_model.count_devices()
        active_count = await self.device_model.count_devices(status="active")
        suspended_count = await self.device_model.count_devices(status="suspended")
        expired_count = await self.device_model.count_devices(status="expired")

        # Obtener dispositivos vivos
        arp_table = await self.router.get_arp_table()
        registered_macs = await self.device_model.get_registered_macs()
        unregistered = sum(1 for arp in arp_table if arp.mac_address not in registered_macs)

        # Health check del router
        health = await self.router.health_check()

        return {
            "total_registered_devices": total_registered,
            "active_devices_now": active_count,
            "suspended_devices": suspended_count,
            "expired_devices": expired_count,
            "unregistered_macs": unregistered,
            "router_latency_ms": health.latency_ms,
            "router_status": health.status,
            "timestamp": datetime.now().isoformat(),
        }

    async def get_top_devices(self, limit: int = 5) -> List[dict]:
        """Obtiene top dispositivos por tráfico."""
        return await self.traffic_model.get_top_devices_by_traffic(limit)

    async def get_network_stats(self, hours: int = 24) -> dict:
        """Obtiene estadísticas de la red."""
        return await self.traffic_model.get_total_network_traffic(hours)

    async def get_alerts(self) -> List[dict]:
        """Obtiene alertas del sistema."""
        alerts = []

        # Alertar sobre dispositivos expirados
        expired = await self.device_model.get_expired_devices()
        for device in expired:
            alerts.append({
                "level": "error",
                "message": f"Dispositivo {device['device_name']} expirado",
                "entity_type": "device",
                "entity_id": str(device["id"]),
                "timestamp": datetime.now().isoformat(),
            })

        # Alertar sobre MACs no registradas
        arp_table = await self.router.get_arp_table()
        registered_macs = await self.device_model.get_registered_macs()
        unregistered = [arp for arp in arp_table if arp.mac_address not in registered_macs]

        for arp in unregistered:
            alerts.append({
                "level": "warning",
                "message": f"MAC no registrada: {arp.mac_address}",
                "entity_type": "mac",
                "entity_id": arp.mac_address,
                "timestamp": datetime.now().isoformat(),
            })

        # Alertar si router no responde
        if await self.router.health_check() and await self.router.health_check().status == "error":
            alerts.append({
                "level": "critical",
                "message": "Router no responde",
                "entity_type": "router",
                "timestamp": datetime.now().isoformat(),
            })

        return alerts[:10]  # Limitar a 10 alertas
