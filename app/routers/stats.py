"""Router de estadísticas para el dashboard."""

from fastapi import APIRouter, Depends, HTTPException, status
from app.models import get_db, Database
from app.dependencies import get_current_user
from datetime import datetime, timedelta

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/dashboard")
async def get_dashboard_stats(
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db),
):
    """Obtiene estadísticas del dashboard."""
    try:
        # Total de usuarios
        users = await db.fetch_all("SELECT COUNT(*) as count FROM users WHERE role = 'user'")
        total_users = users[0][0] if users else 0

        # Usuarios activos (con sesiones)
        active = await db.fetch_all(
            "SELECT COUNT(DISTINCT device_id) FROM sessions WHERE status = 'active'"
        )
        active_users = active[0][0] if active else 0

        # Top consumidores
        top_consumers = await db.fetch_all("""
            SELECT
                u.full_name,
                d.mac_address,
                SUM(s.bytes_in) as bytes_in,
                SUM(s.bytes_out) as bytes_out
            FROM sessions s
            JOIN devices d ON s.device_id = d.id
            JOIN users u ON d.user_id = u.id
            GROUP BY d.id
            ORDER BY (SUM(s.bytes_in) + SUM(s.bytes_out)) DESC
            LIMIT 10
        """)

        top_consumers_data = [
            {
                "full_name": row[0] or "Desconocido",
                "mac_address": row[1],
                "bytes_in": row[2] or 0,
                "bytes_out": row[3] or 0,
            }
            for row in top_consumers
        ]

        # Usuarios por expirar (próximos 7 días)
        soon = (datetime.now() + timedelta(days=7)).isoformat()
        expiring = await db.fetch_all("""
            SELECT full_name, cedula, expires_at
            FROM users
            WHERE expires_at IS NOT NULL
            AND expires_at <= ?
            AND expires_at > datetime('now')
            ORDER BY expires_at ASC
        """, (soon,))

        expiring_data = [
            {
                "full_name": row[0],
                "cedula": row[1],
                "expires_at": row[2],
            }
            for row in expiring
        ]

        return {
            "total_users": total_users,
            "active_users": active_users,
            "top_consumers": top_consumers_data,
            "expiring_soon": expiring_data,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
