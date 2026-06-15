#!/usr/bin/env python3
"""Script para crear usuario admin inicial."""

import asyncio
import sys
from app.models import init_db
from app.auth import hash_password

async def main():
    """Crea usuario admin."""
    print("🔧 Inicializando base de datos...")
    db = await init_db()

    # Crear usuario admin
    username = "admin"
    password = "admin123"
    full_name = "Administrador"

    print(f"\n📝 Creando usuario: {username}")
    print(f"   Contraseña: {password}")
    print(f"   Rol: SUPERADMIN\n")

    password_hash = hash_password(password)

    sql = """
    INSERT INTO users (username, password_hash, full_name, role, status)
    VALUES (?, ?, ?, ?, ?)
    """

    try:
        await db.execute(
            sql,
            (username, password_hash, full_name, "SUPERADMIN", "active"),
        )
        user_id = await db.get_last_insert_rowid()
        print(f"✅ Usuario creado con ID: {user_id}")
        print(f"\n🌐 Accede a http://localhost:8080")
        print(f"   Usuario: {username}")
        print(f"   Contraseña: {password}\n")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(main())
