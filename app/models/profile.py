"""Modelo de perfiles de ancho de banda."""

from typing import Optional, List
from .database import Database


class ProfileModel:
    """Operaciones sobre tabla bandwidth_profiles."""

    def __init__(self, db: Database):
        self.db = db

    async def create_profile(
        self,
        name: str,
        max_upload: Optional[str] = None,
        max_download: Optional[str] = None,
        priority: int = 3,
        description: Optional[str] = None,
    ) -> int:
        """Crea nuevo perfil."""
        sql = """
        INSERT INTO bandwidth_profiles (name, max_upload, max_download, priority, description)
        VALUES (?, ?, ?, ?, ?)
        """
        await self.db.execute(sql, (name, max_upload, max_download, priority, description))
        return await self.db.get_last_insert_rowid()

    async def get_profile_by_id(self, profile_id: int) -> Optional[dict]:
        """Obtiene perfil por ID."""
        sql = "SELECT * FROM bandwidth_profiles WHERE id = ?"
        return await self.db.fetch_one_dict(sql, (profile_id,))

    async def get_profile_by_name(self, name: str) -> Optional[dict]:
        """Obtiene perfil por nombre."""
        sql = "SELECT * FROM bandwidth_profiles WHERE name = ?"
        return await self.db.fetch_one_dict(sql, (name,))

    async def list_profiles(self) -> List[dict]:
        """Lista todos los perfiles."""
        sql = "SELECT * FROM bandwidth_profiles ORDER BY priority ASC, name ASC"
        return await self.db.fetch_all_dict(sql)

    async def update_profile(
        self,
        profile_id: int,
        name: Optional[str] = None,
        max_upload: Optional[str] = None,
        max_download: Optional[str] = None,
        priority: Optional[int] = None,
        description: Optional[str] = None,
    ) -> bool:
        """Actualiza perfil."""
        updates = {}
        if name is not None:
            updates["name"] = name
        if max_upload is not None:
            updates["max_upload"] = max_upload
        if max_download is not None:
            updates["max_download"] = max_download
        if priority is not None:
            updates["priority"] = priority
        if description is not None:
            updates["description"] = description

        if not updates:
            return False

        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        sql = f"UPDATE bandwidth_profiles SET {set_clause} WHERE id = ?"

        params = list(updates.values()) + [profile_id]
        await self.db.execute(sql, tuple(params))
        return True

    async def delete_profile(self, profile_id: int) -> bool:
        """Elimina perfil."""
        sql = "DELETE FROM bandwidth_profiles WHERE id = ?"
        await self.db.execute(sql, (profile_id,))
        return True

    async def get_default_profiles(self) -> List[dict]:
        """Obtiene perfiles por defecto."""
        default_names = ["admin", "profesional", "estandar", "invitado"]
        sql = "SELECT * FROM bandwidth_profiles WHERE name IN (?, ?, ?, ?) ORDER BY priority"
        return await self.db.fetch_all_dict(sql, tuple(default_names))
