"""
Modelo de usuarios (users y operators).

Operaciones CRUD async sobre tabla users.
"""

from typing import Optional, List
from datetime import datetime
from .database import Database


class UserModel:
    """Operaciones sobre tabla users."""

    def __init__(self, db: Database):
        self.db = db

    async def create_user(
        self,
        username: str,
        password_hash: str,
        full_name: str,
        role: str = "user",
        cedula: Optional[str] = None,
        cargo: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        created_by: Optional[int] = None,
    ) -> int:
        """Crea nuevo usuario."""
        sql = """
        INSERT INTO users (username, password_hash, full_name, role, cedula, cargo, email, phone, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        await self.db.execute(
            sql,
            (username, password_hash, full_name, role, cedula, cargo, email, phone, created_by),
        )
        return await self.db.get_last_insert_rowid()

    async def get_user_by_id(self, user_id: int) -> Optional[dict]:
        """Obtiene usuario por ID."""
        sql = "SELECT * FROM users WHERE id = ?"
        return await self.db.fetch_one_dict(sql, (user_id,))

    async def get_user_by_username(self, username: str) -> Optional[dict]:
        """Obtiene usuario por username."""
        sql = "SELECT * FROM users WHERE username = ?"
        return await self.db.fetch_one_dict(sql, (username,))

    async def get_user_by_cedula(self, cedula: str) -> Optional[dict]:
        """Obtiene usuario por cédula."""
        sql = "SELECT * FROM users WHERE cedula = ?"
        return await self.db.fetch_one_dict(sql, (cedula,))

    async def list_users(
        self,
        role: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[dict]:
        """Lista usuarios con filtros."""
        sql = "SELECT * FROM users WHERE 1=1"
        params = []

        if role:
            sql += " AND role = ?"
            params.append(role)
        if status:
            sql += " AND status = ?"
            params.append(status)

        sql += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        return await self.db.fetch_all_dict(sql, tuple(params))

    async def count_users(
        self, role: Optional[str] = None, status: Optional[str] = None
    ) -> int:
        """Cuenta usuarios con filtros."""
        sql = "SELECT COUNT(*) FROM users WHERE 1=1"
        params = []

        if role:
            sql += " AND role = ?"
            params.append(role)
        if status:
            sql += " AND status = ?"
            params.append(status)

        row = await self.db.fetch_one(sql, tuple(params))
        return row[0] if row else 0

    async def update_user(
        self,
        user_id: int,
        **kwargs,
    ) -> bool:
        """Actualiza usuario."""
        allowed_fields = {
            "password_hash",
            "full_name",
            "cedula",
            "cargo",
            "email",
            "phone",
            "role",
            "status",
        }

        fields_to_update = {k: v for k, v in kwargs.items() if k in allowed_fields}
        if not fields_to_update:
            return False

        fields_to_update["updated_at"] = datetime.now().isoformat()

        set_clause = ", ".join([f"{k} = ?" for k in fields_to_update.keys()])
        sql = f"UPDATE users SET {set_clause} WHERE id = ?"

        params = list(fields_to_update.values()) + [user_id]
        await self.db.execute(sql, tuple(params))
        return True

    async def delete_user(self, user_id: int) -> bool:
        """Elimina usuario."""
        sql = "DELETE FROM users WHERE id = ?"
        await self.db.execute(sql, (user_id,))
        return True

    async def disable_user(self, user_id: int) -> bool:
        """Desactiva usuario."""
        return await self.update_user(user_id, status="suspended")

    async def enable_user(self, user_id: int) -> bool:
        """Activa usuario."""
        return await self.update_user(user_id, status="active")

    async def check_expired_users(self) -> List[dict]:
        """Obtiene usuarios expirados."""
        sql = """
        SELECT * FROM users u
        INNER JOIN devices d ON u.id = d.user_id
        WHERE d.expires_at < datetime('now') AND d.status = 'active'
        """
        return await self.db.fetch_all_dict(sql)

    async def mark_user_expired(self, user_id: int) -> bool:
        """Marca usuario como expirado."""
        return await self.update_user(user_id, status="expired")

    async def change_password(self, user_id: int, new_password_hash: str) -> bool:
        """Cambia contraseña."""
        return await self.update_user(user_id, password_hash=new_password_hash)

    async def get_active_users(self) -> List[dict]:
        """Obtiene todos los usuarios activos."""
        sql = "SELECT * FROM users WHERE status = 'active' ORDER BY full_name"
        return await self.db.fetch_all_dict(sql)


class OperatorModel:
    """Operaciones sobre tabla operators."""

    def __init__(self, db: Database):
        self.db = db

    async def create_operator(
        self,
        username: str,
        password_hash: str,
        role: str,
        created_by: Optional[int] = None,
    ) -> int:
        """Crea nuevo operador."""
        sql = """
        INSERT INTO operators (username, password_hash, role, created_by)
        VALUES (?, ?, ?, ?)
        """
        await self.db.execute(sql, (username, password_hash, role, created_by))
        return await self.db.get_last_insert_rowid()

    async def get_operator_by_id(self, operator_id: int) -> Optional[dict]:
        """Obtiene operador por ID."""
        sql = "SELECT * FROM operators WHERE id = ?"
        return await self.db.fetch_one_dict(sql, (operator_id,))

    async def get_operator_by_username(self, username: str) -> Optional[dict]:
        """Obtiene operador por username."""
        sql = "SELECT * FROM operators WHERE username = ?"
        return await self.db.fetch_one_dict(sql, (username,))

    async def list_operators(self, role: Optional[str] = None) -> List[dict]:
        """Lista operadores."""
        sql = "SELECT * FROM operators WHERE 1=1"
        params = []

        if role:
            sql += " AND role = ?"
            params.append(role)

        sql += " ORDER BY created_at DESC"
        return await self.db.fetch_all_dict(sql, tuple(params))

    async def update_operator(
        self,
        operator_id: int,
        **kwargs,
    ) -> bool:
        """Actualiza operador."""
        allowed_fields = {"password_hash", "role", "active"}

        fields_to_update = {k: v for k, v in kwargs.items() if k in allowed_fields}
        if not fields_to_update:
            return False

        set_clause = ", ".join([f"{k} = ?" for k in fields_to_update.keys()])
        sql = f"UPDATE operators SET {set_clause} WHERE id = ?"

        params = list(fields_to_update.values()) + [operator_id]
        await self.db.execute(sql, tuple(params))
        return True

    async def delete_operator(self, operator_id: int) -> bool:
        """Elimina operador."""
        sql = "DELETE FROM operators WHERE id = ?"
        await self.db.execute(sql, (operator_id,))
        return True

    async def update_last_login(self, operator_id: int) -> bool:
        """Actualiza último login."""
        sql = "UPDATE operators SET last_login = datetime('now') WHERE id = ?"
        await self.db.execute(sql, (operator_id,))
        return True

    async def disable_operator(self, operator_id: int) -> bool:
        """Desactiva operador."""
        return await self.update_operator(operator_id, active=False)

    async def enable_operator(self, operator_id: int) -> bool:
        """Activa operador."""
        return await self.update_operator(operator_id, active=True)

    async def get_active_operators(self) -> List[dict]:
        """Obtiene operadores activos."""
        sql = "SELECT * FROM operators WHERE active = 1 ORDER BY username"
        return await self.db.fetch_all_dict(sql)
