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

    # Create tables
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            full_name TEXT,
            email TEXT UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    await conn.execute("""
        CREATE TABLE IF NOT EXISTS devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mac_address TEXT UNIQUE NOT NULL,
            ip_address TEXT,
            hostname TEXT,
            status TEXT DEFAULT 'offline',
            last_seen TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    await conn.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT NOT NULL,
            details TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    await conn.commit()

    # Create default admin user if not exists
    cursor = await conn.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
    result = await cursor.fetchone()

    if result[0] == 0:
        from app.security import hash_password
        admin_hash = hash_password("admin123")
        await conn.execute(
            "INSERT INTO users (username, full_name, email, password_hash, role, is_active) VALUES (?, ?, ?, ?, ?, ?)",
            ("admin", "Administrator", "admin@nac.local", admin_hash, "admin", 1)
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
