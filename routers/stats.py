"""
stats.py — Endpoints para estadísticas y monitoreo
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List

from models import get_db
from routers.auth import get_current_operator
from services import get_dashboard_stats, get_user_stats

router = APIRouter()

@router.get("/dashboard", response_model=dict)
async def get_dashboard(
    db=Depends(get_db),
    operator: dict = Depends(get_current_operator),
):
    """Obtener estadísticas del dashboard"""
    stats = await get_dashboard_stats(db)
    return stats

@router.get("/users/active", response_model=List[dict])
async def get_active_users(
    db=Depends(get_db),
    operator: dict = Depends(get_current_operator),
):
    """Listar usuarios activos (conectados ahora)"""
    from services import routeros
    arp_table = await routeros.get_arp_table()

    active = []
    for entry in arp_table:
        async with db.execute(
            "SELECT id, full_name, cedula FROM users WHERE mac_address = ?",
            (entry["mac"],),
        ) as cursor:
            user = await cursor.fetchone()
            if user:
                active.append({
                    "user_id": user["id"],
                    "full_name": user["full_name"],
                    "cedula": user["cedula"],
                    "mac": entry["mac"],
                    "ip": entry["ip"],
                })

    return active

@router.get("/bandwidth/top", response_model=List[dict])
async def get_top_bandwidth_users(
    db=Depends(get_db),
    operator: dict = Depends(get_current_operator),
    limit: int = 5,
):
    """Obtener top N usuarios por consumo de ancho de banda (últimas 24h)"""
    async with db.execute(
        """SELECT u.id, u.full_name, u.mac_address, SUM(s.bytes_in + s.bytes_out) as total_bytes
        FROM sessions s
        JOIN users u ON s.user_id = u.id
        WHERE s.start_time > datetime('now', '-1 day')
        GROUP BY s.user_id
        ORDER BY total_bytes DESC
        LIMIT ?""",
        (limit,),
    ) as cursor:
        results = [dict(row) for row in await cursor.fetchall()]

    return results

@router.get("/sessions/history", response_model=List[dict])
async def get_session_history(
    db=Depends(get_db),
    operator: dict = Depends(get_current_operator),
    user_id: int = None,
    limit: int = 100,
):
    """Obtener historial de sesiones"""
    query = "SELECT * FROM sessions WHERE 1=1"
    params = []

    if user_id:
        query += " AND user_id = ?"
        params.append(user_id)

    query += " ORDER BY start_time DESC LIMIT ?"
    params.append(limit)

    async with db.execute(query, params) as cursor:
        sessions = [dict(row) for row in await cursor.fetchall()]

    return sessions

@router.get("/audit-log", response_model=List[dict])
async def get_audit_log(
    db=Depends(get_db),
    operator: dict = Depends(get_current_operator),
    limit: int = 100,
    offset: int = 0,
):
    """Obtener log de auditoría"""
    async with db.execute(
        """SELECT * FROM audit_log
        ORDER BY timestamp DESC
        LIMIT ? OFFSET ?""",
        (limit, offset),
    ) as cursor:
        logs = [dict(row) for row in await cursor.fetchall()]

    return logs
