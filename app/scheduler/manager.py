"""
Gestor del Scheduler - Tareas periódicas con APScheduler
"""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.models import Database, get_db
from routeros.client import RouterOSClient
from app.config import get_settings
from .tasks import Tasks

logger = logging.getLogger(__name__)


class SchedulerManager:
    """Gestor central del scheduler"""

    def __init__(self, db: Database, router: RouterOSClient):
        self.db = db
        self.router = router
        self.scheduler = AsyncIOScheduler()
        self.tasks = Tasks(db, router)
        self.settings = get_settings()

    def start(self):
        """Inicia el scheduler con todas las tareas"""
        if self.scheduler.running:
            return

        # Health check - cada 60 segundos
        self.scheduler.add_job(
            self.tasks.health_check,
            trigger=IntervalTrigger(seconds=self.settings.HEALTH_CHECK_INTERVAL),
            name="health_check",
            id="health_check",
            replace_existing=True,
        )

        # Sincronización ARP - cada 5 minutos
        self.scheduler.add_job(
            self.tasks.sync_arp,
            trigger=IntervalTrigger(seconds=self.settings.TRAFFIC_SYNC_INTERVAL),
            name="sync_arp",
            id="sync_arp",
            replace_existing=True,
        )

        # Snapshots de tráfico - cada 5 minutos
        self.scheduler.add_job(
            self.tasks.collect_traffic_snapshots,
            trigger=IntervalTrigger(seconds=self.settings.TRAFFIC_SYNC_INTERVAL),
            name="traffic_snapshots",
            id="traffic_snapshots",
            replace_existing=True,
        )

        # Verificar dispositivos expirados - cada 10 minutos
        self.scheduler.add_job(
            self.tasks.check_expired_devices,
            trigger=IntervalTrigger(seconds=self.settings.EXPIRY_CHECK_INTERVAL),
            name="check_expired_devices",
            id="check_expired_devices",
            replace_existing=True,
        )

        # Actualizar estado de dispositivos vivos - cada 2 minutos
        self.scheduler.add_job(
            self.tasks.update_live_devices,
            trigger=IntervalTrigger(seconds=120),
            name="update_live_devices",
            id="update_live_devices",
            replace_existing=True,
        )

        # Limpiar datos antiguos - cada 24 horas
        self.scheduler.add_job(
            self.tasks.cleanup_old_data,
            trigger=IntervalTrigger(hours=24),
            name="cleanup_old_data",
            id="cleanup_old_data",
            replace_existing=True,
        )

        # Sincronizar queues con router - cada 15 minutos
        self.scheduler.add_job(
            self.tasks.sync_queues,
            trigger=IntervalTrigger(seconds=900),
            name="sync_queues",
            id="sync_queues",
            replace_existing=True,
        )

        self.scheduler.start()
        logger.info("Scheduler iniciado con todas las tareas")

    def stop(self):
        """Detiene el scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler detenido")

    def get_jobs(self):
        """Obtiene lista de tareas activas"""
        return [
            {
                "id": job.id,
                "name": job.name,
                "next_run_time": str(job.next_run_time),
            }
            for job in self.scheduler.get_jobs()
        ]


# Instancia global
_scheduler_manager = None


async def init_scheduler(db: Database, router: RouterOSClient):
    """Inicializa scheduler global"""
    global _scheduler_manager
    _scheduler_manager = SchedulerManager(db, router)
    _scheduler_manager.start()
    return _scheduler_manager


async def get_scheduler():
    """Obtiene scheduler global"""
    if not _scheduler_manager:
        raise RuntimeError("Scheduler no inicializado")
    return _scheduler_manager


async def stop_scheduler():
    """Detiene scheduler global"""
    global _scheduler_manager
    if _scheduler_manager:
        _scheduler_manager.stop()
