"""
Inicialización y gestión de base de datos SQLite.

Proporciona:
- Inicialización de todas las tablas
- Connection pool
- Métodos de utilidad
"""

import sqlite3
import logging
from pathlib import Path
from typing import Optional
import aiosqlite

logger = logging.getLogger(__name__)


class Database:
    """Gestor de base de datos SQLite."""

    def __init__(self, db_path: str = "data/db.sqlite3"):
        """
        Inicializa BD.

        Args:
            db_path: Ruta del archivo SQLite
        """
        self.db_path = db_path
        self.conn: Optional[aiosqlite.Connection] = None

    async def init(self) -> None:
        """Abre conexión y crea tablas si no existen."""
        # Crear directorio si no existe
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        # Abrir conexión
        self.conn = await aiosqlite.connect(self.db_path)
        await self.conn.execute("PRAGMA foreign_keys = ON")
        await self.conn.commit()

        # Crear tablas
        await self._create_tables()

        # Crear datos iniciales
        await self._create_initial_data()

        logger.info(f"Base de datos inicializada: {self.db_path}")

    async def close(self) -> None:
        """Cierra conexión a BD."""
        if self.conn:
            await self.conn.close()
            logger.info("Conexión a BD cerrada")

    async def _create_tables(self) -> None:
        """Crea todas las tablas."""
        if not self.conn:
            raise RuntimeError("BD no inicializada")

        tables = [
            self._create_users_table(),
            self._create_operators_table(),
            self._create_devices_table(),
            self._create_bandwidth_profiles_table(),
            self._create_sessions_table(),
            self._create_traffic_snapshots_table(),
            self._create_dns_categories_table(),
            self._create_dns_entries_table(),
            self._create_audit_log_table(),
            self._create_router_sync_log_table(),
        ]

        for sql in tables:
            try:
                statements = [s.strip() for s in sql.split(';') if s.strip()]
                for stmt in statements:
                    await self.conn.execute(stmt)
                await self.conn.commit()
            except sqlite3.OperationalError as e:
                if "already exists" in str(e):
                    logger.debug(f"Tabla ya existe: {e}")
                else:
                    raise

    async def _create_initial_data(self) -> None:
        """Crea datos iniciales (usuario admin, categorías DNS, etc)."""
        if not self.conn:
            raise RuntimeError("BD no inicializada")

        try:
            # Crear usuario admin si no existe
            admin_exists = await self.conn.execute(
                "SELECT id FROM users WHERE username = 'admin' LIMIT 1"
            )
            admin_row = await admin_exists.fetchone()

            if not admin_row:
                # Importar aquí para evitar circular imports
                from app.auth import hash_password

                password_hash = hash_password("admin123")
                await self.conn.execute(
                    """
                    INSERT INTO users (username, password_hash, full_name, role, status)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    ("admin", password_hash, "Administrador", "SUPERADMIN", "active"),
                )
                await self.conn.commit()
                logger.info("Usuario admin creado: admin/admin123")

            # Crear categorías DNS por defecto
            categories = [
                ("Redes Sociales", "Bloquear redes sociales", "#FF6B6B"),
                ("Streaming", "Bloquear sitios de streaming", "#4ECDC4"),
                ("Juegos", "Bloquear sitios de juegos", "#45B7D1"),
                ("Productividad", "Permitir sitios de productividad", "#96CEB4"),
            ]

            for name, desc, color in categories:
                exists = await self.conn.execute(
                    "SELECT id FROM dns_categories WHERE name = ? LIMIT 1",
                    (name,),
                )
                if not await exists.fetchone():
                    await self.conn.execute(
                        """
                        INSERT INTO dns_categories (name, description, color)
                        VALUES (?, ?, ?)
                        """,
                        (name, desc, color),
                    )

            await self.conn.commit()

        except Exception as e:
            logger.error(f"Error creando datos iniciales: {e}")
            # No fallar si los datos ya existen

    @staticmethod
    def _create_users_table() -> str:
        """SQL: tabla users."""
        return """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            cedula TEXT UNIQUE,
            cargo TEXT,
            email TEXT,
            phone TEXT,
            role TEXT NOT NULL DEFAULT 'user',
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER,
            FOREIGN KEY (created_by) REFERENCES users(id)
        );
        CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
        CREATE INDEX IF NOT EXISTS idx_users_cedula ON users(cedula);
        CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
        CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);
        """

    @staticmethod
    def _create_operators_table() -> str:
        """SQL: tabla operators."""
        return """
        CREATE TABLE IF NOT EXISTS operators (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER,
            last_login TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES operators(id)
        );
        CREATE INDEX IF NOT EXISTS idx_operators_username ON operators(username);
        CREATE INDEX IF NOT EXISTS idx_operators_role ON operators(role);
        """

    @staticmethod
    def _create_devices_table() -> str:
        """SQL: tabla devices."""
        return """
        CREATE TABLE IF NOT EXISTS devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mac_address TEXT UNIQUE NOT NULL,
            device_name TEXT NOT NULL,
            device_type TEXT,
            user_id INTEGER,
            profile_id INTEGER,
            assigned_ip TEXT,
            status TEXT DEFAULT 'active',
            last_seen TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            comment TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (profile_id) REFERENCES bandwidth_profiles(id)
        );
        CREATE INDEX IF NOT EXISTS idx_devices_mac ON devices(mac_address);
        CREATE INDEX IF NOT EXISTS idx_devices_user ON devices(user_id);
        CREATE INDEX IF NOT EXISTS idx_devices_status ON devices(status);
        """

    @staticmethod
    def _create_bandwidth_profiles_table() -> str:
        """SQL: tabla bandwidth_profiles."""
        return """
        CREATE TABLE IF NOT EXISTS bandwidth_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            max_upload TEXT,
            max_download TEXT,
            priority INTEGER DEFAULT 3,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """

    @staticmethod
    def _create_sessions_table() -> str:
        """SQL: tabla sessions (sesiones activas e históricas)."""
        return """
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id INTEGER NOT NULL,
            start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            end_time TIMESTAMP,
            duration_seconds INTEGER,
            bytes_in INTEGER DEFAULT 0,
            bytes_out INTEGER DEFAULT 0,
            packets_in INTEGER DEFAULT 0,
            packets_out INTEGER DEFAULT 0,
            status TEXT DEFAULT 'active',
            FOREIGN KEY (device_id) REFERENCES devices(id)
        );
        CREATE INDEX IF NOT EXISTS idx_sessions_device ON sessions(device_id);
        CREATE INDEX IF NOT EXISTS idx_sessions_start ON sessions(start_time);
        CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);
        """

    @staticmethod
    def _create_traffic_snapshots_table() -> str:
        """SQL: tabla traffic_snapshots (snapshot de tráfico cada 5 min)."""
        return """
        CREATE TABLE IF NOT EXISTS traffic_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id INTEGER NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            bytes_in INTEGER,
            bytes_out INTEGER,
            packets_in INTEGER,
            packets_out INTEGER,
            FOREIGN KEY (device_id) REFERENCES devices(id)
        );
        CREATE INDEX IF NOT EXISTS idx_traffic_device ON traffic_snapshots(device_id);
        CREATE INDEX IF NOT EXISTS idx_traffic_timestamp ON traffic_snapshots(timestamp);
        """

    @staticmethod
    def _create_dns_categories_table() -> str:
        """SQL: tabla dns_categories."""
        return """
        CREATE TABLE IF NOT EXISTS dns_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            color TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """

    @staticmethod
    def _create_dns_entries_table() -> str:
        """SQL: tabla dns_entries."""
        return """
        CREATE TABLE IF NOT EXISTS dns_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER,
            domain TEXT UNIQUE NOT NULL,
            address TEXT DEFAULT '0.0.0.0',
            enabled BOOLEAN DEFAULT 1,
            comment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES dns_categories(id)
        );
        CREATE INDEX IF NOT EXISTS idx_dns_domain ON dns_entries(domain);
        CREATE INDEX IF NOT EXISTS idx_dns_category ON dns_entries(category_id);
        """

    @staticmethod
    def _create_audit_log_table() -> str:
        """SQL: tabla audit_log."""
        return """
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            operator_id INTEGER,
            action TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            entity_id TEXT,
            entity_name TEXT,
            result TEXT DEFAULT 'success',
            details TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (operator_id) REFERENCES operators(id)
        );
        CREATE INDEX IF NOT EXISTS idx_audit_operator ON audit_log(operator_id);
        CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_log(action);
        CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp);
        """

    @staticmethod
    def _create_router_sync_log_table() -> str:
        """SQL: tabla router_sync_log."""
        return """
        CREATE TABLE IF NOT EXISTS router_sync_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            action TEXT NOT NULL,
            status TEXT NOT NULL,
            message TEXT,
            latency_ms REAL,
            details TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_router_sync_timestamp ON router_sync_log(timestamp);
        """

    async def execute(self, sql: str, params: tuple = ()):
        """Ejecuta SQL sin retornar resultados."""
        if not self.conn:
            raise RuntimeError("BD no inicializada")
        await self.conn.execute(sql, params)
        await self.conn.commit()

    async def execute_many(self, sql: str, params_list: list):
        """Ejecuta SQL múltiples veces."""
        if not self.conn:
            raise RuntimeError("BD no inicializada")
        await self.conn.executemany(sql, params_list)
        await self.conn.commit()

    async def fetch_one(self, sql: str, params: tuple = ()):
        """Obtiene una fila."""
        if not self.conn:
            raise RuntimeError("BD no inicializada")
        async with self.conn.execute(sql, params) as cursor:
            return await cursor.fetchone()

    async def fetch_all(self, sql: str, params: tuple = ()):
        """Obtiene todas las filas."""
        if not self.conn:
            raise RuntimeError("BD no inicializada")
        async with self.conn.execute(sql, params) as cursor:
            return await cursor.fetchall()

    async def fetch_one_dict(self, sql: str, params: tuple = ()) -> Optional[dict]:
        """Obtiene una fila como diccionario."""
        if not self.conn:
            raise RuntimeError("BD no inicializada")
        self.conn.row_factory = sqlite3.Row
        async with self.conn.execute(sql, params) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def fetch_all_dict(self, sql: str, params: tuple = ()) -> list:
        """Obtiene todas las filas como diccionarios."""
        if not self.conn:
            raise RuntimeError("BD no inicializada")
        self.conn.row_factory = sqlite3.Row
        async with self.conn.execute(sql, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_last_insert_rowid(self) -> int:
        """Obtiene ID de último insert."""
        if not self.conn:
            raise RuntimeError("BD no inicializada")
        cursor = await self.conn.execute("SELECT last_insert_rowid()")
        row = await cursor.fetchone()
        return row[0] if row else 0


# Singleton
_db: Optional[Database] = None


async def init_db(db_path: str = "data/db.sqlite3") -> Database:
    """Inicializa base de datos global."""
    global _db
    _db = Database(db_path)
    await _db.init()
    return _db


async def get_db() -> Database:
    """Obtiene instancia de BD (dependency injection)."""
    global _db
    if not _db:
        raise RuntimeError("BD no inicializada")
    return _db


async def close_db() -> None:
    """Cierra BD global."""
    global _db
    if _db:
        await _db.close()
