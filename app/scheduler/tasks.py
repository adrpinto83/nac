"""
Tareas periódicas del Scheduler
"""

import logging
from datetime import datetime
from app.models import (
    Database,
    DeviceModel,
    SessionModel,
    TrafficModel,
    RouterSyncLogModel,
    AuditLogModel,
)
from routeros.client import RouterOSClient

logger = logging.getLogger(__name__)


class Tasks:
    """Conjunto de tareas periódicas"""

    def __init__(self, db: Database, router: RouterOSClient):
        self.db = db
        self.router = router

    async def health_check(self):
        """Health check del router cada 60 segundos"""
        try:
            start = datetime.now()
            health = await self.router.health_check()
            latency = (datetime.now() - start).total_seconds() * 1000

            status = "ok" if health.status == "ok" else "error"

            sync_log = RouterSyncLogModel(self.db)
            await sync_log.log_health_check(latency, status == "ok")

            if status == "error":
                logger.warning(f"Router health check failed: {health.message}")

        except Exception as e:
            logger.error(f"Error en health check: {e}")
            sync_log = RouterSyncLogModel(self.db)
            await sync_log.log_sync("health_check", "error", str(e))

    async def sync_arp(self):
        """Sincroniza ARP table cada 5 minutos"""
        try:
            device_model = DeviceModel(self.db)
            sync_log = RouterSyncLogModel(self.db)

            # Obtener ARP del router
            arp_table = await self.router.get_arp_table()

            # Actualizar last_seen de dispositivos registrados
            for arp_entry in arp_table:
                device = await device_model.get_device_by_mac(arp_entry.mac_address)
                if device:
                    await device_model.update_last_seen(device["id"])

            await sync_log.log_arp_sync("ok", len(arp_table))
            logger.info(f"ARP sync completado: {len(arp_table)} dispositivos")

        except Exception as e:
            logger.error(f"Error en ARP sync: {e}")
            sync_log = RouterSyncLogModel(self.db)
            await sync_log.log_arp_sync("error", 0)

    async def collect_traffic_snapshots(self):
        """Recolecta snapshots de tráfico cada 5 minutos"""
        try:
            device_model = DeviceModel(self.db)
            traffic_model = TrafficModel(self.db)

            # Obtener todas las interfaces
            interfaces = await self.router.get_interfaces()

            for iface in interfaces:
                # Buscar dispositivo por interfaz
                devices = await device_model.get_active_devices()
                for device in devices:
                    # En producción, mapear MAC a interfaz
                    # Por ahora, usar bytes estimados
                    await traffic_model.insert_snapshot(
                        device_id=device["id"],
                        bytes_in=0,  # Sería obtenido del router
                        bytes_out=0,
                        packets_in=0,
                        packets_out=0,
                    )

            logger.info("Traffic snapshots recolectados")

        except Exception as e:
            logger.error(f"Error recolectando snapshots: {e}")

    async def check_expired_devices(self):
        """Verifica y marca dispositivos expirados"""
        try:
            device_model = DeviceModel(self.db)

            # Obtener dispositivos expirados
            expired = await device_model.get_expired_devices()

            for device in expired:
                # Marcar como expirado
                await device_model.mark_expired(device["id"])

                # Bloquear en router
                try:
                    await self.router.add_to_address_list(
                        list_name="mac-blacklist",
                        address=device["mac_address"],
                        comment=f"Expirado: {device['device_name']}",
                    )
                except Exception as e:
                    logger.error(f"Error bloqueando dispositivo expirado: {e}")

            if expired:
                logger.info(f"Marcados {len(expired)} dispositivos como expirados")

        except Exception as e:
            logger.error(f"Error verificando dispositivos expirados: {e}")

    async def update_live_devices(self):
        """Actualiza estado de dispositivos vivos cada 2 minutos"""
        try:
            device_model = DeviceModel(self.db)

            # Obtener ARP actual
            arp_table = await self.router.get_arp_table()
            registered_macs = await device_model.get_registered_macs()

            # Actualizar dispositivos que NO están en ARP (offline)
            devices = await device_model.get_active_devices()
            for device in devices:
                is_online = any(arp.mac_address == device["mac_address"] for arp in arp_table)
                if not is_online:
                    # Cerrar sesión activa si existe
                    session_model = SessionModel(self.db)
                    active = await session_model.get_device_active_session(device["id"])
                    if active:
                        await session_model.end_session(active["id"])

            logger.debug(f"Estados actualizados: {len(devices)} dispositivos")

        except Exception as e:
            logger.error(f"Error actualizando dispositivos vivos: {e}")

    async def sync_queues(self):
        """Sincroniza QoS queues cada 15 minutos"""
        try:
            device_model = DeviceModel(self.db)
            sync_log = RouterSyncLogModel(self.db)

            # Obtener dispositivos con perfil
            devices = await device_model.get_active_devices()
            queue_count = 0

            for device in devices:
                if device.get("profile_id"):
                    # Obtener o crear queue en router
                    try:
                        queue_name = f"{device['device_name']}-qos"
                        # Verificar si existe
                        queues = await self.router.get_simple_queues()
                        exists = any(q.name == queue_name for q in queues)

                        if not exists:
                            await self.router.create_queue(
                                name=queue_name,
                                target=device.get("assigned_ip", "192.168.88.0/24"),
                                max_limit="10M/5M",  # Default
                            )
                            queue_count += 1
                    except Exception as e:
                        logger.error(f"Error sincronizando queue: {e}")

            await sync_log.log_queue_sync("ok", queue_count)
            logger.info(f"QoS sync completado: {queue_count} queues")

        except Exception as e:
            logger.error(f"Error en QoS sync: {e}")
            sync_log = RouterSyncLogModel(self.db)
            await sync_log.log_queue_sync("error", 0)

    async def cleanup_old_data(self):
        """Limpia datos antiguos cada 24 horas"""
        try:
            traffic_model = TrafficModel(self.db)
            sync_log = RouterSyncLogModel(self.db)

            # Limpiar snapshots de tráfico (> 30 días)
            await traffic_model.cleanup_old_snapshots(days=30)

            # Limpiar router sync log (> 7 días)
            await sync_log.cleanup_old_entries(days=7)

            logger.info("Limpieza de datos antiguos completada")

        except Exception as e:
            logger.error(f"Error limpiando datos: {e}")

    async def sync_dns_entries(self):
        """Sincroniza entradas DNS bloqueadas con router"""
        try:
            from app.models.dns_entry import DNSEntryModel

            dns_model = DNSEntryModel(self.db)
            entries = await dns_model.list_entries()

            sync_count = 0
            for entry in entries:
                if entry.get("enabled"):
                    try:
                        await self.router.add_dns_entry(
                            entry["domain"],
                            entry.get("address", "0.0.0.0"),
                        )
                        sync_count += 1
                    except Exception as e:
                        logger.warning(f"Error sincronizando DNS {entry['domain']}: {e}")

            logger.info(f"DNS sync completado: {sync_count} entradas")

        except Exception as e:
            logger.error(f"Error en DNS sync: {e}")
