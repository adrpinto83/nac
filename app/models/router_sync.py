"""Modelo de log de sincronización del router."""

from typing import List, Optional
from .database import Database


class RouterSyncLogModel:
    """Operaciones sobre tabla router_sync_log."""

    def __init__(self, db: Database):
        self.db = db

    async def log_sync(
        self,
        action: str,
        status: str,
        message: Optional[str] = None,
        latency_ms: Optional[float] = None,
        details: Optional[str] = None,
    ) -> int:
        """Registra sincronización con router."""
        sql = """
        INSERT INTO router_sync_log (action, status, message, latency_ms, details)
        VALUES (?, ?, ?, ?, ?)
        """
        await self.db.execute(sql, (action, status, message, latency_ms, details))
        return await self.db.get_last_insert_rowid()

    async def get_recent_syncs(self, hours: int = 24, limit: int = 100) -> List[dict]:
        """Obtiene sincronizaciones recientes."""
        sql = """
        SELECT * FROM router_sync_log
        WHERE timestamp > datetime('now', '-' || ? || ' hours')
        ORDER BY timestamp DESC
        LIMIT ?
        """
        return await self.db.fetch_all_dict(sql, (hours, limit))

    async def get_last_sync(self) -> Optional[dict]:
        """Obtiene última sincronización."""
        sql = "SELECT * FROM router_sync_log ORDER BY timestamp DESC LIMIT 1"
        return await self.db.fetch_one_dict(sql)

    async def get_sync_by_action(self, action: str, hours: int = 24) -> List[dict]:
        """Obtiene sincronizaciones por acción."""
        sql = """
        SELECT * FROM router_sync_log
        WHERE action = ? AND timestamp > datetime('now', '-' || ? || ' hours')
        ORDER BY timestamp DESC
        """
        return await self.db.fetch_all_dict(sql, (action, hours))

    async def get_failed_syncs(self, limit: int = 50) -> List[dict]:
        """Obtiene sincronizaciones fallidas."""
        sql = """
        SELECT * FROM router_sync_log
        WHERE status = 'error'
        ORDER BY timestamp DESC
        LIMIT ?
        """
        return await self.db.fetch_all_dict(sql, (limit,))

    async def get_sync_stats(self, hours: int = 24) -> dict:
        """Obtiene estadísticas de sincronización."""
        sql = """
        SELECT
            COUNT(*) as total_syncs,
            SUM(CASE WHEN status = 'ok' THEN 1 ELSE 0 END) as ok_count,
            SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as error_count,
            AVG(latency_ms) as avg_latency,
            MAX(latency_ms) as max_latency,
            MIN(latency_ms) as min_latency
        FROM router_sync_log
        WHERE timestamp > datetime('now', '-' || ? || ' hours')
        """
        row = await self.db.fetch_one_dict(sql, (hours,))
        return {
            "total": row["total_syncs"] or 0,
            "ok": row["ok_count"] or 0,
            "error": row["error_count"] or 0,
            "avg_latency_ms": row["avg_latency"],
            "max_latency_ms": row["max_latency"],
            "min_latency_ms": row["min_latency"],
        }

    async def get_router_health(self) -> dict:
        """Obtiene estado de salud del router."""
        last = await self.get_last_sync()
        if not last:
            return {"status": "unknown", "message": "No data"}

        return {
            "status": last["status"],
            "message": last["message"],
            "latency_ms": last["latency_ms"],
            "timestamp": last["timestamp"],
        }

    async def cleanup_old_entries(self, days: int = 7) -> int:
        """Elimina entradas más antiguas que N días."""
        sql = "DELETE FROM router_sync_log WHERE timestamp < datetime('now', '-' || ? || ' days')"
        await self.db.execute(sql, (days,))
        return 1

    async def log_health_check(self, latency_ms: float, ok: bool) -> int:
        """Registra health check."""
        status = "ok" if ok else "error"
        message = "Health check passed" if ok else "Health check failed"
        return await self.log_sync("health_check", status, message, latency_ms)

    async def log_arp_sync(self, status: str, device_count: int) -> int:
        """Registra sincronización de ARP."""
        message = f"Synced {device_count} devices"
        return await self.log_sync("arp_sync", status, message, None, f"devices: {device_count}")

    async def log_queue_sync(self, status: str, queue_count: int) -> int:
        """Registra sincronización de queues."""
        message = f"Synced {queue_count} queues"
        return await self.log_sync("queue_sync", status, message, None, f"queues: {queue_count}")

    async def log_dns_sync(self, status: str, entry_count: int) -> int:
        """Registra sincronización de DNS."""
        message = f"Synced {entry_count} DNS entries"
        return await self.log_sync("dns_sync", status, message, None, f"entries: {entry_count}")
