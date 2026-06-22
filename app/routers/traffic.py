"""Endpoints para consumo de ancho de banda por usuario."""

from fastapi import APIRouter, HTTPException, Header
from typing import Optional
from app.database import get_db
from app.security import decode_token

router = APIRouter(prefix="/traffic", tags=["traffic"])


async def verify_token(authorization: Optional[str]):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="No autenticado")
    payload = decode_token(authorization.split(" ")[1])
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido")
    return payload


def _fmt_bytes(b: int) -> dict:
    """Convierte bytes a unidad legible."""
    if b >= 1_073_741_824:
        return {"value": round(b / 1_073_741_824, 2), "unit": "GB"}
    if b >= 1_048_576:
        return {"value": round(b / 1_048_576, 2), "unit": "MB"}
    if b >= 1024:
        return {"value": round(b / 1024, 2), "unit": "KB"}
    return {"value": b, "unit": "B"}


@router.get("/users")
async def get_traffic_per_user(authorization: Optional[str] = Header(None)):
    """Retorna consumo acumulado de ancho de banda por usuario."""
    payload = await verify_token(authorization)

    db = await get_db()
    try:
        # Verificar rol del llamante
        cur = await db.execute(
            "SELECT role FROM users WHERE username = ?", (payload.get("sub"),)
        )
        caller = await cur.fetchone()
        if not caller or caller[0] != "admin":
            raise HTTPException(status_code=403, detail="Solo administradores")

        # Intentar leer datos en tiempo real del router (hotspot active)
        live_data: dict[str, dict] = {}
        try:
            from app.services.mikrotik_client import MikroTikClient
            client = MikroTikClient()
            sessions = await client.get_hotspot_active()
            for s in sessions:
                live_data[s.user] = {
                    "bytes_in": s.bytes_in,
                    "bytes_out": s.bytes_out,
                    "address": s.address,
                    "uptime": s.uptime,
                    "online": True,
                }
        except Exception:
            pass  # Si el router no está disponible, solo mostramos datos históricos

        # Datos históricos de la tabla traffic_usage
        cur = await db.execute("""
            SELECT u.id, u.username, u.full_name,
                   COALESCE(SUM(t.bytes_down), 0) as total_down,
                   COALESCE(SUM(t.bytes_up), 0)   as total_up,
                   MAX(t.recorded_at) as last_seen
            FROM users u
            LEFT JOIN traffic_usage t ON t.user_id = u.id
            WHERE u.role = 'user' AND u.approval_status = 'approved'
            GROUP BY u.id
            ORDER BY (total_down + total_up) DESC
        """)
        rows = await cur.fetchall()

        result = []
        for row in rows:
            uid, uname, fname, hist_down, hist_up, last_seen = row
            live = live_data.get(uname, {})
            total_down = hist_down + live.get("bytes_in", 0)
            total_up   = hist_up   + live.get("bytes_out", 0)
            result.append({
                "user_id":    uid,
                "username":   uname,
                "full_name":  fname,
                "online":     live.get("online", False),
                "ip_address": live.get("address"),
                "uptime":     live.get("uptime"),
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


@router.post("/snapshot")
async def save_traffic_snapshot(authorization: Optional[str] = Header(None)):
    """Guarda un snapshot del tráfico actual desde el router."""
    payload = await verify_token(authorization)

    db = await get_db()
    try:
        cur = await db.execute(
            "SELECT role FROM users WHERE username = ?", (payload.get("sub"),)
        )
        caller = await cur.fetchone()
        if not caller or caller[0] != "admin":
            raise HTTPException(status_code=403, detail="Solo administradores")

        saved = 0
        try:
            from app.services.mikrotik_client import MikroTikClient
            client = MikroTikClient()
            sessions = await client.get_hotspot_active()
            for s in sessions:
                cur = await db.execute(
                    "SELECT id FROM users WHERE username = ?", (s.user,)
                )
                user_row = await cur.fetchone()
                if user_row and (s.bytes_in > 0 or s.bytes_out > 0):
                    await db.execute(
                        "INSERT INTO traffic_usage (user_id, bytes_down, bytes_up) VALUES (?, ?, ?)",
                        (user_row[0], s.bytes_in, s.bytes_out),
                    )
                    saved += 1
            await db.commit()
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Error al leer router: {e}")

        return {"saved": saved}
    finally:
        await db.close()
