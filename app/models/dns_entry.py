"""Modelo de entradas DNS."""

from typing import Optional, List
from .database import Database


class DNSCategoryModel:
    """Operaciones sobre tabla dns_categories."""

    def __init__(self, db: Database):
        self.db = db

    async def create_category(self, name: str, description: Optional[str] = None) -> int:
        """Crea categoría DNS."""
        sql = "INSERT INTO dns_categories (name, description) VALUES (?, ?)"
        await self.db.execute(sql, (name, description))
        return await self.db.get_last_insert_rowid()

    async def list_categories(self) -> List[dict]:
        """Lista todas las categorías."""
        sql = "SELECT * FROM dns_categories ORDER BY name"
        return await self.db.fetch_all_dict(sql)

    async def get_category(self, category_id: int) -> Optional[dict]:
        """Obtiene categoría."""
        sql = "SELECT * FROM dns_categories WHERE id = ?"
        return await self.db.fetch_one_dict(sql, (category_id,))

    async def delete_category(self, category_id: int) -> bool:
        """Elimina categoría."""
        sql = "DELETE FROM dns_categories WHERE id = ?"
        await self.db.execute(sql, (category_id,))
        return True


class DNSEntryModel:
    """Operaciones sobre tabla dns_entries."""

    def __init__(self, db: Database):
        self.db = db

    async def create_entry(
        self, domain: str, category_id: Optional[int] = None, comment: Optional[str] = None
    ) -> int:
        """Crea entrada DNS."""
        sql = "INSERT INTO dns_entries (domain, category_id, comment) VALUES (?, ?, ?)"
        await self.db.execute(sql, (domain, category_id, comment))
        return await self.db.get_last_insert_rowid()

    async def list_entries(self, category_id: Optional[int] = None) -> List[dict]:
        """Lista entradas DNS."""
        if category_id:
            sql = "SELECT * FROM dns_entries WHERE category_id = ? ORDER BY domain"
            return await self.db.fetch_all_dict(sql, (category_id,))
        else:
            sql = "SELECT * FROM dns_entries ORDER BY domain"
            return await self.db.fetch_all_dict(sql)

    async def get_entry(self, entry_id: int) -> Optional[dict]:
        """Obtiene entrada."""
        sql = "SELECT * FROM dns_entries WHERE id = ?"
        return await self.db.fetch_one_dict(sql, (entry_id,))

    async def delete_entry(self, entry_id: int) -> bool:
        """Elimina entrada."""
        sql = "DELETE FROM dns_entries WHERE id = ?"
        await self.db.execute(sql, (entry_id,))
        return True

    async def domain_exists(self, domain: str) -> bool:
        """Verifica si dominio existe."""
        row = await self.db.fetch_one("SELECT id FROM dns_entries WHERE domain = ?", (domain,))
        return row is not None

    async def get_entries_by_category(self, category_id: int) -> List[dict]:
        """Obtiene entradas de una categoría."""
        sql = """
        SELECT e.* FROM dns_entries e
        WHERE e.category_id = ? AND e.enabled = 1
        ORDER BY e.domain
        """
        return await self.db.fetch_all_dict(sql, (category_id,))

    async def count_entries(self, category_id: Optional[int] = None) -> int:
        """Cuenta entradas."""
        if category_id:
            row = await self.db.fetch_one(
                "SELECT COUNT(*) FROM dns_entries WHERE category_id = ?", (category_id,)
            )
        else:
            row = await self.db.fetch_one("SELECT COUNT(*) FROM dns_entries")
        return row[0] if row else 0

    async def enable_entry(self, entry_id: int) -> bool:
        """Habilita entrada."""
        sql = "UPDATE dns_entries SET enabled = 1 WHERE id = ?"
        await self.db.execute(sql, (entry_id,))
        return True

    async def disable_entry(self, entry_id: int) -> bool:
        """Deshabilita entrada."""
        sql = "UPDATE dns_entries SET enabled = 0 WHERE id = ?"
        await self.db.execute(sql, (entry_id,))
        return True
