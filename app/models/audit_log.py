"""Modelo de log de auditoría."""

from typing import List, Optional
from .database import Database


class AuditLogModel:
    """Operaciones sobre tabla audit_log."""

    def __init__(self, db: Database):
        self.db = db

    async def log_action(
        self,
        operator_id: Optional[int],
        action: str,
        entity_type: str,
        entity_id: Optional[str] = None,
        entity_name: Optional[str] = None,
        result: str = "success",
        details: Optional[str] = None,
    ) -> int:
        """Registra acción en auditoría."""
        sql = """
        INSERT INTO audit_log (operator_id, action, entity_type, entity_id, entity_name, result, details)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        await self.db.execute(
            sql, (operator_id, action, entity_type, entity_id, entity_name, result, details)
        )
        return await self.db.get_last_insert_rowid()

    async def get_log_entries(
        self,
        operator_id: Optional[int] = None,
        action: Optional[str] = None,
        entity_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[dict]:
        """Obtiene entradas del log con filtros."""
        sql = "SELECT * FROM audit_log WHERE 1=1"
        params = []

        if operator_id:
            sql += " AND operator_id = ?"
            params.append(operator_id)
        if action:
            sql += " AND action = ?"
            params.append(action)
        if entity_type:
            sql += " AND entity_type = ?"
            params.append(entity_type)

        sql += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        return await self.db.fetch_all_dict(sql, tuple(params))

    async def count_entries(
        self,
        operator_id: Optional[int] = None,
        action: Optional[str] = None,
        entity_type: Optional[str] = None,
    ) -> int:
        """Cuenta entradas del log."""
        sql = "SELECT COUNT(*) FROM audit_log WHERE 1=1"
        params = []

        if operator_id:
            sql += " AND operator_id = ?"
            params.append(operator_id)
        if action:
            sql += " AND action = ?"
            params.append(action)
        if entity_type:
            sql += " AND entity_type = ?"
            params.append(entity_type)

        row = await self.db.fetch_one(sql, tuple(params))
        return row[0] if row else 0

    async def get_operator_actions(self, operator_id: int, limit: int = 50) -> List[dict]:
        """Obtiene acciones de un operador."""
        sql = """
        SELECT * FROM audit_log
        WHERE operator_id = ?
        ORDER BY timestamp DESC
        LIMIT ?
        """
        return await self.db.fetch_all_dict(sql, (operator_id, limit))

    async def get_entity_history(self, entity_type: str, entity_id: str) -> List[dict]:
        """Obtiene historial de una entidad."""
        sql = """
        SELECT * FROM audit_log
        WHERE entity_type = ? AND entity_id = ?
        ORDER BY timestamp DESC
        """
        return await self.db.fetch_all_dict(sql, (entity_type, entity_id))

    async def cleanup_old_entries(self, days: int = 90) -> int:
        """Elimina entradas más antiguas que N días."""
        sql = "DELETE FROM audit_log WHERE timestamp < datetime('now', '-' || ? || ' days')"
        await self.db.execute(sql, (days,))
        return 1

    async def get_failed_actions(self, limit: int = 50) -> List[dict]:
        """Obtiene acciones fallidas."""
        sql = """
        SELECT * FROM audit_log
        WHERE result = 'failure'
        ORDER BY timestamp DESC
        LIMIT ?
        """
        return await self.db.fetch_all_dict(sql, (limit,))

    async def get_actions_summary(self, hours: int = 24) -> dict:
        """Obtiene resumen de acciones."""
        sql = """
        SELECT
            action,
            COUNT(*) as count,
            SUM(CASE WHEN result = 'success' THEN 1 ELSE 0 END) as success_count,
            SUM(CASE WHEN result = 'failure' THEN 1 ELSE 0 END) as failure_count
        FROM audit_log
        WHERE timestamp > datetime('now', '-' || ? || ' hours')
        GROUP BY action
        ORDER BY count DESC
        """
        rows = await self.db.fetch_all_dict(sql, (hours,))
        return {row["action"]: row for row in rows}
