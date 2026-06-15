"""
Modelo de dispositivos.

Operaciones CRUD async sobre tabla devices.
"""

from typing import Optional, List
from datetime import datetime
from .database import Database


class DeviceModel:
    """Operaciones sobre tabla devices."""

    def __init__(self, db: Database):
        self.db = db

    async def create_device(
        self,
        mac_address: str,
        device_name: str,
        user_id: int,
        profile_id: Optional[int] = None,
        device_type: Optional[str] = None,
        assigned_ip: Optional[str] = None,
        expires_at: Optional[str] = None,
        comment: Optional[str] = None,
    ) -> int:
        """Crea nuevo dispositivo."""
        sql = """
        INSERT INTO devices (mac_address, device_name, user_id, profile_id, device_type, assigned_ip, expires_at, comment)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        await self.db.execute(
            sql,
            (mac_address, device_name, user_id, profile_id, device_type, assigned_ip, expires_at, comment),
        )
        return await self.db.get_last_insert_rowid()

    async def get_device_by_id(self, device_id: int) -> Optional[dict]:
        """Obtiene dispositivo por ID."""
        sql = "SELECT * FROM devices WHERE id = ?"
        return await self.db.fetch_one_dict(sql, (device_id,))

    async def get_device_by_mac(self, mac_address: str) -> Optional[dict]:
        """Obtiene dispositivo por MAC."""
        sql = "SELECT * FROM devices WHERE mac_address = ?"
        return await self.db.fetch_one_dict(sql, (mac_address,))

    async def get_devices_by_user(self, user_id: int) -> List[dict]:
        """Obtiene dispositivos de un usuario."""
        sql = "SELECT * FROM devices WHERE user_id = ? ORDER BY created_at DESC"
        return await self.db.fetch_all_dict(sql, (user_id,))

    async def list_devices(
        self,
        status: Optional[str] = None,
        device_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[dict]:
        """Lista dispositivos con filtros."""
        sql = "SELECT * FROM devices WHERE 1=1"
        params = []

        if status:
            sql += " AND status = ?"
            params.append(status)
        if device_type:
            sql += " AND device_type = ?"
            params.append(device_type)

        sql += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        return await self.db.fetch_all_dict(sql, tuple(params))

    async def count_devices(
        self, status: Optional[str] = None, device_type: Optional[str] = None
    ) -> int:
        """Cuenta dispositivos con filtros."""
        sql = "SELECT COUNT(*) FROM devices WHERE 1=1"
        params = []

        if status:
            sql += " AND status = ?"
            params.append(status)
        if device_type:
            sql += " AND device_type = ?"
            params.append(device_type)

        row = await self.db.fetch_one(sql, tuple(params))
        return row[0] if row else 0

    async def update_device(
        self,
        device_id: int,
        **kwargs,
    ) -> bool:
        """Actualiza dispositivo."""
        allowed_fields = {
            "device_name",
            "user_id",
            "profile_id",
            "assigned_ip",
            "status",
            "expires_at",
            "comment",
        }

        fields_to_update = {k: v for k, v in kwargs.items() if k in allowed_fields}
        if not fields_to_update:
            return False

        fields_to_update["updated_at"] = datetime.now().isoformat()
        fields_to_update["last_seen"] = datetime.now().isoformat()

        set_clause = ", ".join([f"{k} = ?" for k in fields_to_update.keys()])
        sql = f"UPDATE devices SET {set_clause} WHERE id = ?"

        params = list(fields_to_update.values()) + [device_id]
        await self.db.execute(sql, tuple(params))
        return True

    async def delete_device(self, device_id: int) -> bool:
        """Elimina dispositivo."""
        sql = "DELETE FROM devices WHERE id = ?"
        await self.db.execute(sql, (device_id,))
        return True

    async def suspend_device(self, device_id: int) -> bool:
        """Suspende dispositivo."""
        return await self.update_device(device_id, status="suspended")

    async def unsuspend_device(self, device_id: int) -> bool:
        """Reactiva dispositivo suspendido."""
        return await self.update_device(device_id, status="active")

    async def block_device(self, device_id: int) -> bool:
        """Bloquea dispositivo."""
        return await self.update_device(device_id, status="blocked")

    async def unblock_device(self, device_id: int) -> bool:
        """Desbloquea dispositivo."""
        return await self.update_device(device_id, status="active")

    async def update_last_seen(self, device_id: int) -> bool:
        """Actualiza última vista."""
        sql = "UPDATE devices SET last_seen = datetime('now') WHERE id = ?"
        await self.db.execute(sql, (device_id,))
        return True

    async def change_device_profile(self, device_id: int, profile_id: int) -> bool:
        """Cambia perfil QoS de dispositivo."""
        return await self.update_device(device_id, profile_id=profile_id)

    async def get_active_devices(self) -> List[dict]:
        """Obtiene dispositivos activos."""
        sql = "SELECT * FROM devices WHERE status = 'active' ORDER BY device_name"
        return await self.db.fetch_all_dict(sql)

    async def get_registered_macs(self) -> List[str]:
        """Obtiene todas las MACs registradas."""
        sql = "SELECT DISTINCT mac_address FROM devices WHERE status = 'active'"
        rows = await self.db.fetch_all(sql)
        return [row[0] for row in rows]

    async def search_devices(self, query: str) -> List[dict]:
        """Busca dispositivos por nombre, MAC o usuario."""
        sql = """
        SELECT d.*, u.full_name, p.name as profile_name
        FROM devices d
        LEFT JOIN users u ON d.user_id = u.id
        LEFT JOIN bandwidth_profiles p ON d.profile_id = p.id
        WHERE d.device_name LIKE ? OR d.mac_address LIKE ? OR u.full_name LIKE ?
        ORDER BY d.created_at DESC
        """
        search_term = f"%{query}%"
        return await self.db.fetch_all_dict(sql, (search_term, search_term, search_term))

    async def get_devices_by_profile(self, profile_id: int) -> List[dict]:
        """Obtiene dispositivos de un perfil."""
        sql = "SELECT * FROM devices WHERE profile_id = ?"
        return await self.db.fetch_all_dict(sql, (profile_id,))

    async def get_devices_expiring_soon(self, days: int = 7) -> List[dict]:
        """Obtiene dispositivos que expiran pronto."""
        sql = """
        SELECT d.*, u.full_name
        FROM devices d
        LEFT JOIN users u ON d.user_id = u.id
        WHERE d.expires_at IS NOT NULL
        AND d.expires_at > datetime('now')
        AND d.expires_at < datetime('now', '+' || ? || ' days')
        AND d.status = 'active'
        ORDER BY d.expires_at ASC
        """
        return await self.db.fetch_all_dict(sql, (days,))

    async def get_expired_devices(self) -> List[dict]:
        """Obtiene dispositivos expirados."""
        sql = """
        SELECT * FROM devices
        WHERE expires_at IS NOT NULL
        AND expires_at < datetime('now')
        AND status = 'active'
        """
        return await self.db.fetch_all_dict(sql)

    async def mark_expired(self, device_id: int) -> bool:
        """Marca dispositivo como expirado."""
        return await self.update_device(device_id, status="expired")

    async def get_device_with_user(self, device_id: int) -> Optional[dict]:
        """Obtiene dispositivo con información de usuario."""
        sql = """
        SELECT d.*, u.full_name, u.cedula, u.email, p.name as profile_name
        FROM devices d
        LEFT JOIN users u ON d.user_id = u.id
        LEFT JOIN bandwidth_profiles p ON d.profile_id = p.id
        WHERE d.id = ?
        """
        return await self.db.fetch_one_dict(sql, (device_id,))

    async def get_all_devices_with_info(self) -> List[dict]:
        """Obtiene todos los dispositivos con información completa."""
        sql = """
        SELECT d.*, u.full_name, u.cedula, u.email, p.name as profile_name
        FROM devices d
        LEFT JOIN users u ON d.user_id = u.id
        LEFT JOIN bandwidth_profiles p ON d.profile_id = p.id
        ORDER BY d.created_at DESC
        """
        return await self.db.fetch_all_dict(sql)
