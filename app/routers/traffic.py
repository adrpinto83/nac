"""Endpoints para consumo de ancho de banda por usuario."""

import os
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Header, Query
from pydantic import BaseModel
from typing import Optional, List
from app.database import get_db
from app.security import decode_token

router = APIRouter(prefix="/traffic", tags=["traffic"])

SYNC_KEY = os.environ.get("NAC_SYNC_KEY", "nac-sync-2024")

# Cache en memoria de la última sesión reportada por el router (se refresca cada 60s)
_latest_sessions: dict[str, dict] = {}
_last_report_at: Optional[str] = None


async def verify_token(authorization: Optional[str]):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="No autenticado")
    payload = decode_token(authorization.split(" ")[1])
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido")
    return payload


def _fmt_bytes(b: int) -> dict:
    if b >= 1_073_741_824:
        return {"value": round(b / 1_073_741_824, 2), "unit": "GB"}
    if b >= 1_048_576:
        return {"value": round(b / 1_048_576, 2), "unit": "MB"}
    if b >= 1024:
        return {"value": round(b / 1024, 2), "unit": "KB"}
    return {"value": b, "unit": "B"}


class SessionReport(BaseModel):
    user: str
    address: str = ""
    mac_address: str = ""
    uptime: str = ""
    bytes_in: int = 0
    bytes_out: int = 0


class TrafficReportRequest(BaseModel):
    sessions: List[SessionReport]


@router.post("/report")
async def receive_traffic_report(
    body: TrafficReportRequest,
    x_sync_key: Optional[str] = Header(None),
):
    """
    Endpoint que el router MikroTik llama para reportar sesiones activas.
    Actualiza la tabla traffic_usage con el consumo de cada usuario.
    """
    if x_sync_key != SYNC_KEY:
        raise HTTPException(status_code=403, detail="Clave de sincronización inválida")

    db = await get_db()
    try:
        saved = 0
        for s in body.sessions:
            if s.bytes_in == 0 and s.bytes_out == 0:
                continue

            # El router envía la MAC como campo 'user' y también en 'mac_address'
            mac = (s.mac_address or s.user or "").upper().strip()
            if not mac:
                continue

            # Buscar usuario por MAC en la tabla devices
            cur = await db.execute(
                "SELECT user_id FROM devices WHERE UPPER(mac_address) = ?", (mac,)
            )
            device_row = await cur.fetchone()
            if not device_row:
                continue

            user_id = device_row[0]

            await db.execute(
                "INSERT INTO traffic_usage (user_id, bytes_down, bytes_up) VALUES (?, ?, ?)",
                (user_id, s.bytes_in, s.bytes_out)
            )
            await db.execute(
                "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
                (user_id,)
            )
            saved += 1

        await db.commit()

        # Actualizar cache en memoria con las sesiones actuales del router
        global _latest_sessions, _last_report_at
        _latest_sessions = {
            s.mac_address.upper(): {
                "user":        s.user,
                "address":     s.address,
                "mac_address": s.mac_address,
                "uptime":      s.uptime,
                "bytes_in":    s.bytes_in,
                "bytes_out":   s.bytes_out,
            }
            for s in body.sessions
            if s.mac_address
        }
        _last_report_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        return {"ok": True, "saved": saved}
    finally:
        await db.close()


@router.get("/live")
async def get_live_sessions(key: str = Query(default="")):
    """
    Sesiones activas en tiempo real tal como el router las reportó (última vez).
    Autenticado con sync_key — no requiere login de admin.
    """
    if key != SYNC_KEY:
        raise HTTPException(status_code=403, detail="Clave inválida")

    sessions = list(_latest_sessions.values())
    return {
        "last_report_at": _last_report_at,
        "session_count":  len(sessions),
        "sessions":       sessions,
    }


@router.get("/users")
async def get_traffic_per_user(authorization: Optional[str] = Header(None)):
    """Retorna consumo acumulado de ancho de banda por usuario."""
    payload = await verify_token(authorization)

    db = await get_db()
    try:
        cur = await db.execute(
            "SELECT role FROM users WHERE username = ?", (payload.get("sub"),)
        )
        caller = await cur.fetchone()
        if not caller or caller[0] != "admin":
            raise HTTPException(status_code=403, detail="Solo administradores")

        # Sesiones activas reportadas recientemente (últimos 5 minutos)
        cur = await db.execute("""
            SELECT u.id, u.username, u.full_name,
                   COALESCE(SUM(t.bytes_down), 0) as total_down,
                   COALESCE(SUM(t.bytes_up), 0)   as total_up,
                   MAX(t.recorded_at) as last_seen
            FROM users u
            LEFT JOIN traffic_usage t ON t.user_id = u.id
            WHERE u.role = 'user' AND u.approval_status = 'approved'
            GROUP BY u.id
            ORDER BY (COALESCE(SUM(t.bytes_down),0) + COALESCE(SUM(t.bytes_up),0)) DESC
        """)
        rows = await cur.fetchall()

        # Usuarios vistos en los últimos 10 minutos = "online"
        cur_online = await db.execute("""
            SELECT DISTINCT user_id FROM traffic_usage
            WHERE recorded_at >= datetime('now', '-10 minutes')
        """)
        online_ids = {r[0] for r in await cur_online.fetchall()}

        result = []
        for row in rows:
            uid, uname, fname, total_down, total_up, last_seen = row
            total_down = total_down or 0
            total_up   = total_up   or 0
            result.append({
                "user_id":    uid,
                "username":   uname,
                "full_name":  fname,
                "online":     uid in online_ids,
                "bytes_down": total_down,
                "bytes_up":   total_up,
                "bytes_total": total_down + total_up,
                "down_fmt":   _fmt_bytes(total_down),
                "up_fmt":     _fmt_bytes(total_up),
                "total_fmt":  _fmt_bytes(total_down + total_up),
                "last_seen":  last_seen,
            })

        return result
    finally:
        await db.close()
