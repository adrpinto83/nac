"""
services.py — Lógica de negocio (business logic)
"""

import aiosqlite
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from routeros_client import RouterOSClient
import logging

logger = logging.getLogger(__name__)

# Cliente RouterOS global (se inicializa al arrancar la app)
routeros = None

async def init_routeros_client():
    """Inicializar cliente RouterOS"""
    global routeros
    routeros = RouterOSClient()
    try:
        await routeros.connect()
        is_connected = await routeros.test_connection()
        if is_connected:
            logger.info("✓ Conectado a RouterOS correctamente")
        else:
            logger.error("✗ No se puede conectar a RouterOS")
    except Exception as e:
        logger.error(f"✗ Error conectando a RouterOS: {e}")

# ============ USER SERVICES ============

async def create_user(
    db: aiosqlite.Connection,
    full_name: str,
    cedula: str,
    mac_address: str,
    profile: str = "ESTANDAR",
    cargo: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    asset_tag: Optional[str] = None,
    device_type: str = "PC",
    expires_at: Optional[datetime] = None,
) -> Tuple[bool, Optional[int], str]:
    """Crear nuevo usuario y agregar a whitelist en RouterOS"""
    try:
        # Verificar que la MAC no exista
        async with db.execute(
            "SELECT id FROM users WHERE mac_address = ?", (mac_address,)
        ) as cursor:
            if await cursor.fetchone():
                return False, None, "MAC ya registrada"

        # Verificar que la cédula no exista
        async with db.execute(
            "SELECT id FROM users WHERE cedula = ?", (cedula,)
        ) as cursor:
            if await cursor.fetchone():
                return False, None, "Cédula ya registrada"

        # Insertar en BD
        cursor = await db.execute(
            """INSERT INTO users
            (full_name, cedula, cargo, email, phone, asset_tag, device_type, mac_address, profile, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                full_name,
                cedula,
                cargo,
                email,
                phone,
                asset_tag,
                device_type,
                mac_address,
                profile,
                expires_at,
            ),
        )
        user_id = cursor.lastrowid
        await db.commit()

        # Agregar a whitelist en RouterOS
        await routeros.add_mac_to_whitelist(
            mac_address, f"{full_name} ({cedula})"
        )

        # Crear DHCP lease
        ip_range = "192.168.88.50"  # IP estática para el usuario
        await routeros.create_dhcp_lease(mac_address, ip_range, full_name)

        # Crear QoS queue
        queue_name = f"user-{user_id}"
        if profile == "ADMIN":
            max_limit = "0/0"
        elif profile == "PROFESIONAL":
            max_limit = "10M/5M"
        elif profile == "ESTANDAR":
            max_limit = "5M/2M"
        else:  # INVITADO
            max_limit = "2M/1M"

        await routeros.create_queue(queue_name, ip_range, max_limit, priority=3)

        return True, user_id, f"Usuario {full_name} creado exitosamente"

    except Exception as e:
        logger.error(f"Error creando usuario: {e}")
        return False, None, str(e)

async def update_user(
    db: aiosqlite.Connection,
    user_id: int,
    **kwargs
) -> Tuple[bool, str]:
    """Actualizar usuario y sincronizar cambios a RouterOS"""
    try:
        # Actualizar BD
        set_clause = ", ".join([f"{k} = ?" for k in kwargs.keys()])
        await db.execute(
            f"UPDATE users SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (*kwargs.values(), user_id),
        )
        await db.commit()

        # Obtener usuario actualizado
        async with db.execute("SELECT * FROM users WHERE id = ?", (user_id,)) as cursor:
            user = await cursor.fetchone()

        # Sincronizar con RouterOS si cambió el perfil
        if "profile" in kwargs:
            queue_name = f"user-{user_id}"
            max_limit = {
                "ADMIN": "0/0",
                "PROFESIONAL": "10M/5M",
                "ESTANDAR": "5M/2M",
                "INVITADO": "2M/1M",
            }.get(kwargs["profile"], "5M/2M")
            await routeros.update_queue(queue_name, max_limit)

        # Sincronizar estado
        if "status" in kwargs:
            mac = user["mac_address"]
            if kwargs["status"] == "suspendido":
                await routeros.add_mac_to_blocklist(mac, f"Suspended: {user['full_name']}")
            else:
                await routeros.remove_mac_from_blocklist(mac)

        return True, "Usuario actualizado"

    except Exception as e:
        logger.error(f"Error actualizando usuario: {e}")
        return False, str(e)

async def delete_user(db: aiosqlite.Connection, user_id: int) -> Tuple[bool, str]:
    """Eliminar usuario y remover de RouterOS"""
    try:
        # Obtener datos del usuario
        async with db.execute("SELECT * FROM users WHERE id = ?", (user_id,)) as cursor:
            user = await cursor.fetchone()

        if not user:
            return False, "Usuario no encontrado"

        # Remover de whitelists
        await routeros.remove_mac_from_whitelist(user["mac_address"])
        await routeros.remove_mac_from_blocklist(user["mac_address"])

        # Eliminar DHCP lease
        await routeros.delete_dhcp_lease(user["mac_address"])

        # Eliminar queue
        queue_name = f"user-{user_id}"
        await routeros.delete_queue(queue_name)

        # Eliminar de BD
        await db.execute("DELETE FROM users WHERE id = ?", (user_id,))
        await db.commit()

        return True, f"Usuario {user['full_name']} eliminado"

    except Exception as e:
        logger.error(f"Error eliminando usuario: {e}")
        return False, str(e)

# ============ STATISTICS SERVICES ============

async def get_user_stats(
    db: aiosqlite.Connection, user_id: int
) -> Optional[Dict]:
    """Obtener estadísticas de un usuario"""
    try:
        async with db.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ) as cursor:
            user = await cursor.fetchone()

        if not user:
            return None

        # Obtener estado online desde ARP
        arp_table = await routeros.get_arp_table()
        is_online = any(entry["mac"] == user["mac_address"] for entry in arp_table)

        # Obtener bytes de la queue
        queue_name = f"user-{user_id}"
        queue_stats = await routeros.get_queue_stats(queue_name)

        return {
            "user_id": user_id,
            "full_name": user["full_name"],
            "mac_address": user["mac_address"],
            "is_online": is_online,
            "bytes_in": queue_stats.get("bytes_in", 0),
            "bytes_out": queue_stats.get("bytes_out", 0),
            "profile": user["profile"],
            "status": user["status"],
        }

    except Exception as e:
        logger.error(f"Error obteniendo stats: {e}")
        return None

async def get_dashboard_stats(db: aiosqlite.Connection) -> Dict:
    """Obtener estadísticas del dashboard"""
    try:
        # Total usuarios
        async with db.execute("SELECT COUNT(*) as count FROM users") as cursor:
            total_users = (await cursor.fetchone())["count"]

        # Usuarios activos
        arp_table = await routeros.get_arp_table()
        arp_macs = {entry["mac"] for entry in arp_table}

        async with db.execute("SELECT COUNT(*) as count FROM users WHERE mac_address IN (?)", (arp_macs,)) as cursor:
            active_users = (await cursor.fetchone())["count"] if arp_macs else 0

        # Top consumidores (últimas 24h)
        async with db.execute(
            """SELECT user_id, SUM(bytes_in + bytes_out) as total_bytes
            FROM sessions
            WHERE start_time > datetime('now', '-1 day')
            GROUP BY user_id
            ORDER BY total_bytes DESC
            LIMIT 5"""
        ) as cursor:
            top_rows = await cursor.fetchall()

        top_consumers = []
        for row in top_rows:
            user_stats = await get_user_stats(db, row["user_id"])
            if user_stats:
                top_consumers.append(user_stats)

        # Usuarios con expiración próxima (< 7 días)
        async with db.execute(
            """SELECT * FROM users
            WHERE expires_at IS NOT NULL
            AND expires_at < datetime('now', '+7 days')
            ORDER BY expires_at ASC"""
        ) as cursor:
            expiring = [dict(row) for row in await cursor.fetchall()]

        return {
            "total_users": total_users,
            "active_users": active_users,
            "top_consumers": top_consumers,
            "expiring_soon": expiring,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error obteniendo dashboard stats: {e}")
        return {}

# ============ DNS SERVICES ============

async def update_user_dns_categories(
    db: aiosqlite.Connection,
    user_id: int,
    category_ids: List[int],
) -> Tuple[bool, str]:
    """Actualizar categorías DNS bloqueadas para un usuario"""
    try:
        # Limpiar categorías anteriores
        await db.execute("DELETE FROM user_dns_categories WHERE user_id = ?", (user_id,))

        # Agregar nuevas categorías
        for cat_id in category_ids:
            await db.execute(
                "INSERT INTO user_dns_categories (user_id, category_id) VALUES (?, ?)",
                (user_id, cat_id),
            )

        await db.commit()

        # Sincronizar con RouterOS
        async with db.execute(
            """SELECT d.domain FROM dns_entries d
            JOIN user_dns_categories udc ON d.category_id = udc.category_id
            WHERE udc.user_id = ?""",
            (user_id,),
        ) as cursor:
            domains = [row["domain"] for row in await cursor.fetchall()]

        for domain in domains:
            await routeros.add_dns_entry(domain)

        return True, "Categorías DNS actualizadas"

    except Exception as e:
        logger.error(f"Error actualizando DNS: {e}")
        return False, str(e)

async def add_dns_entry_to_category(
    db: aiosqlite.Connection,
    category_id: int,
    domain: str,
) -> Tuple[bool, str]:
    """Agregar dominio a categoría DNS"""
    try:
        # Verificar que la categoría existe
        async with db.execute(
            "SELECT id FROM dns_categories WHERE id = ?", (category_id,)
        ) as cursor:
            if not await cursor.fetchone():
                return False, "Categoría no encontrada"

        # Agregar entrada
        await db.execute(
            "INSERT INTO dns_entries (category_id, domain) VALUES (?, ?)",
            (category_id, domain),
        )
        await db.commit()

        # Agregar a RouterOS
        await routeros.add_dns_entry(domain)

        return True, f"Dominio {domain} agregado"

    except Exception as e:
        logger.error(f"Error agregando DNS entry: {e}")
        return False, str(e)

# ============ AUDIT SERVICES ============

async def log_audit(
    db: aiosqlite.Connection,
    operator_id: Optional[int],
    action: str,
    resource_type: Optional[str] = None,
    resource_id: Optional[int] = None,
    status: str = "success",
    details: Optional[str] = None,
) -> bool:
    """Registrar acción de auditoría"""
    try:
        await db.execute(
            """INSERT INTO audit_log
            (operator_id, action, resource_type, resource_id, status, details)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (operator_id, action, resource_type, resource_id, status, details),
        )
        await db.commit()
        return True
    except Exception as e:
        logger.error(f"Error registrando audit: {e}")
        return False
