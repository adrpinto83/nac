"""Modelo de snapshots de tráfico."""

from typing import List
from .database import Database


class TrafficModel:
    """Operaciones sobre tabla traffic_snapshots."""

    def __init__(self, db: Database):
        self.db = db

    async def insert_snapshot(
        self, device_id: int, bytes_in: int, bytes_out: int, packets_in: int = 0, packets_out: int = 0
    ) -> int:
        """Inserta snapshot de tráfico."""
        sql = """
        INSERT INTO traffic_snapshots (device_id, bytes_in, bytes_out, packets_in, packets_out)
        VALUES (?, ?, ?, ?, ?)
        """
        await self.db.execute(sql, (device_id, bytes_in, bytes_out, packets_in, packets_out))
        return await self.db.get_last_insert_rowid()

    async def get_device_traffic(self, device_id: int, hours: int = 24) -> List[dict]:
        """Obtiene historial de tráfico (últimas N horas)."""
        sql = """
        SELECT * FROM traffic_snapshots
        WHERE device_id = ?
        AND timestamp > datetime('now', '-' || ? || ' hours')
        ORDER BY timestamp ASC
        """
        return await self.db.fetch_all_dict(sql, (device_id, hours))

    async def get_total_bytes(self, device_id: int, hours: int = 24) -> dict:
        """Obtiene total de bytes en período."""
        sql = """
        SELECT
            SUM(bytes_in) as total_bytes_in,
            SUM(bytes_out) as total_bytes_out,
            MAX(bytes_in) as max_bytes_in,
            MAX(bytes_out) as max_bytes_out
        FROM traffic_snapshots
        WHERE device_id = ?
        AND timestamp > datetime('now', '-' || ? || ' hours')
        """
        row = await self.db.fetch_one_dict(sql, (device_id, hours))
        return {
            "bytes_in": row["total_bytes_in"] or 0,
            "bytes_out": row["total_bytes_out"] or 0,
            "max_in": row["max_bytes_in"] or 0,
            "max_out": row["max_bytes_out"] or 0,
        }

    async def cleanup_old_snapshots(self, days: int = 30) -> int:
        """Elimina snapshots más antiguos que N días."""
        sql = """
        DELETE FROM traffic_snapshots
        WHERE timestamp < datetime('now', '-' || ? || ' days')
        """
        await self.db.execute(sql, (days,))
        return 1

    async def get_top_devices_by_traffic(self, limit: int = 10) -> List[dict]:
        """Obtiene dispositivos con más tráfico (últimas 24h)."""
        sql = """
        SELECT d.id, d.mac_address, d.device_name, u.full_name,
               SUM(t.bytes_in) as total_bytes_in,
               SUM(t.bytes_out) as total_bytes_out
        FROM traffic_snapshots t
        JOIN devices d ON t.device_id = d.id
        LEFT JOIN users u ON d.user_id = u.id
        WHERE t.timestamp > datetime('now', '-1 hour')
        GROUP BY t.device_id
        ORDER BY total_bytes_in + total_bytes_out DESC
        LIMIT ?
        """
        return await self.db.fetch_all_dict(sql, (limit,))

    async def get_total_network_traffic(self, hours: int = 24) -> dict:
        """Obtiene tráfico total de la red."""
        sql = """
        SELECT
            SUM(bytes_in) as total_bytes_in,
            SUM(bytes_out) as total_bytes_out,
            COUNT(DISTINCT device_id) as device_count
        FROM traffic_snapshots
        WHERE timestamp > datetime('now', '-' || ? || ' hours')
        """
        row = await self.db.fetch_one_dict(sql, (hours,))
        return {
            "bytes_in": row["total_bytes_in"] or 0,
            "bytes_out": row["total_bytes_out"] or 0,
            "devices": row["device_count"] or 0,
        }
