"""Database management with SQLite."""

import sqlite3
from pathlib import Path
from typing import Optional
import aiosqlite

DB_PATH = "data/db.sqlite3"


async def init_db():
    """Initialize database and create tables."""
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)

    conn = await aiosqlite.connect(DB_PATH)
    await conn.execute("PRAGMA foreign_keys = ON")

    # Users table - Enhanced with more fields
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE,
            phone TEXT,
            department TEXT,
            position TEXT,
            company TEXT,
            ticket_number TEXT,
            access_duration_hours INTEGER,
            access_expires_at TIMESTAMP,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            is_active BOOLEAN DEFAULT 1,
            approval_status TEXT DEFAULT 'pending',
            last_login TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Migración: agregar columnas si la tabla ya existe sin ellas
    for col, defn in [
        ('ticket_number', 'TEXT'),
        ('access_duration_hours', 'INTEGER'),
        ('access_expires_at', 'TIMESTAMP'),
        ('department', 'TEXT'),
        ('position', 'TEXT'),
    ]:
        try:
            await conn.execute(f'ALTER TABLE users ADD COLUMN {col} {defn}')
        except Exception:
            pass  # columna ya existe

    # Device types table
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS device_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Devices table - Enhanced with user relationship
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            mac_address TEXT NOT NULL,
            ip_address TEXT,
            hostname TEXT,
            device_type TEXT,
            manufacturer TEXT,
            model TEXT,
            serial_number TEXT,
            os_type TEXT,
            os_version TEXT,
            status TEXT DEFAULT 'offline',
            last_seen TIMESTAMP,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE(mac_address)
        )
    """)

    # Audit log table - Enhanced
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT NOT NULL,
            entity_type TEXT,
            entity_id INTEGER,
            details TEXT,
            ip_address TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
        )
    """)

    # Sessions table - Track user sessions
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token_hash TEXT NOT NULL,
            ip_address TEXT,
            user_agent TEXT,
            expires_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    await conn.commit()

    # Insert default device types
    await conn.execute("INSERT OR IGNORE INTO device_types (name, description) VALUES ('laptop', 'Laptop Computer')")
    await conn.execute("INSERT OR IGNORE INTO device_types (name, description) VALUES ('desktop', 'Desktop Computer')")
    await conn.execute("INSERT OR IGNORE INTO device_types (name, description) VALUES ('smartphone', 'Mobile Phone')")
    await conn.execute("INSERT OR IGNORE INTO device_types (name, description) VALUES ('tablet', 'Tablet Device')")
    await conn.execute("INSERT OR IGNORE INTO device_types (name, description) VALUES ('printer', 'Network Printer')")
    await conn.execute("INSERT OR IGNORE INTO device_types (name, description) VALUES ('router', 'Network Router')")
    await conn.execute("INSERT OR IGNORE INTO device_types (name, description) VALUES ('other', 'Other Device')")
    await conn.commit()

    # Create default admin user if not exists
    cursor = await conn.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
    result = await cursor.fetchone()

    if result[0] == 0:
        from app.security import hash_password
        admin_hash = hash_password("admin123")
        await conn.execute(
            """INSERT INTO users
               (username, full_name, email, phone, department, position, company, password_hash, role, is_active, approval_status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            ("admin", "Administrator", "admin@nac.local", "+1234567890", "IT", "System Administrator",
             "Company", admin_hash, "admin", 1, "approved")
        )
        await conn.commit()

    await conn.close()
    return True


async def get_db():
    """Get database connection."""
    return await aiosqlite.connect(DB_PATH)


async def close_db(conn):
    """Close database connection."""
    if conn:
        await conn.close()
