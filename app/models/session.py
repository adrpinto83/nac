"""Modelo de sesiones activas."""

from typing import Optional, List
from datetime import datetime
from .database import Database


class SessionModel:
    """Operaciones sobre tabla sessions."""

    def __init__(self, db: Database):
        self.db = db

    async def create_session(self, device_id: int) -> int:
        """Crea nueva sesión activa."""
        sql = "INSERT INTO sessions (device_id, status) VALUES (?, ?)"
        await self.db.execute(sql, (device_id, "active"))
        return await self.db.get_last_insert_rowid()

    async def get_session(self, session_id: int) -> Optional[dict]:
        """Obtiene sesión."""
        sql = "SELECT * FROM sessions WHERE id = ?"
        return await self.db.fetch_one_dict(sql, (session_id,))

    async def get_active_sessions(self) -> List[dict]:
        """Obtiene sesiones activas."""
        sql = "SELECT * FROM sessions WHERE status = 'active' ORDER BY start_time DESC"
        return await self.db.fetch_all_dict(sql)

    async def get_sessions_by_device(self, device_id: int) -> List[dict]:
        """Obtiene historial de sesiones de un dispositivo."""
        sql = """
        SELECT * FROM sessions
        WHERE device_id = ?
        ORDER BY start_time DESC
        LIMIT 100
        """
        return await self.db.fetch_all_dict(sql, (device_id,))

    async def end_session(self, session_id: int, bytes_in: int = 0, bytes_out: int = 0) -> bool:
        """Finaliza sesión."""
        sql = """
        UPDATE sessions
        SET end_time = datetime('now'),
            status = 'closed',
            bytes_in = ?,
            bytes_out = ?,
            duration_seconds = (SELECT (julianday('now') - julianday(start_time)) * 86400)
        WHERE id = ?
        """
        await self.db.execute(sql, (bytes_in, bytes_out, session_id))
        return True

    async def update_session_bytes(self, session_id: int, bytes_in: int, bytes_out: int) -> bool:
        """Actualiza bytes de sesión activa."""
        sql = "UPDATE sessions SET bytes_in = ?, bytes_out = ? WHERE id = ?"
        await self.db.execute(sql, (bytes_in, bytes_out, session_id))
        return True

    async def get_device_active_session(self, device_id: int) -> Optional[dict]:
        """Obtiene sesión activa de dispositivo."""
        sql = "SELECT * FROM sessions WHERE device_id = ? AND status = 'active'"
        return await self.db.fetch_one_dict(sql, (device_id,))

    async def close_device_sessions(self, device_id: int) -> int:
        """Cierra todas las sesiones activas de un dispositivo."""
        sql = """
        UPDATE sessions
        SET end_time = datetime('now'),
            status = 'closed',
            duration_seconds = (SELECT (julianday('now') - julianday(start_time)) * 86400)
        WHERE device_id = ? AND status = 'active'
        """
        await self.db.execute(sql, (device_id,))
        return await self.db.get_last_insert_rowid()

    async def count_active_sessions(self) -> int:
        """Cuenta sesiones activas."""
        row = await self.db.fetch_one("SELECT COUNT(*) FROM sessions WHERE status = 'active'")
        return row[0] if row else 0

    async def get_session_duration(self, session_id: int) -> Optional[int]:
        """Obtiene duración de sesión en segundos."""
        sql = """
        SELECT CASE
            WHEN status = 'active' THEN CAST((julianday('now') - julianday(start_time)) * 86400 AS INTEGER)
            ELSE duration_seconds
        END
        FROM sessions
        WHERE id = ?
        """
        row = await self.db.fetch_one(sql, (session_id,))
        return row[0] if row else None
