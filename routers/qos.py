"""
qos.py — Endpoints para gestión de perfiles de ancho de banda
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from models import get_db
from routers.auth import get_current_operator
from services import log_audit

router = APIRouter()

@router.get("/profiles", response_model=List[dict])
async def get_bandwidth_profiles(
    db=Depends(get_db),
    operator: dict = Depends(get_current_operator),
):
    """Listar perfiles de QoS disponibles"""
    async with db.execute(
        "SELECT * FROM bandwidth_profiles WHERE enabled = 1 ORDER BY priority"
    ) as cursor:
        profiles = [dict(row) for row in await cursor.fetchall()]

    return profiles

@router.get("/{profile_id}", response_model=dict)
async def get_profile_details(
    profile_id: int,
    db=Depends(get_db),
    operator: dict = Depends(get_current_operator),
):
    """Obtener detalles de un perfil"""
    async with db.execute(
        "SELECT * FROM bandwidth_profiles WHERE id = ?", (profile_id,)
    ) as cursor:
        profile = await cursor.fetchone()

    if not profile:
        raise HTTPException(status_code=404, detail="Perfil no encontrado")

    return dict(profile)

@router.put("/{profile_id}", response_model=dict)
async def update_profile(
    profile_id: int,
    max_limit_down: str,
    max_limit_up: str,
    priority: int,
    db=Depends(get_db),
    operator: dict = Depends(get_current_operator),
):
    """Actualizar perfil QoS (solo SUPERADMIN)"""
    if operator["role"] != "SUPERADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo SUPERADMIN puede modificar perfiles",
        )

    await db.execute(
        """UPDATE bandwidth_profiles
        SET max_limit_down = ?, max_limit_up = ?, priority = ?
        WHERE id = ?""",
        (max_limit_down, max_limit_up, priority, profile_id),
    )
    await db.commit()

    await log_audit(
        db, operator["id"], "UPDATE_PROFILE", "bandwidth_profile", profile_id,
        details=f"Down: {max_limit_down}, Up: {max_limit_up}"
    )

    return {"message": "Perfil actualizado"}

@router.get("/user/{user_id}/current-profile", response_model=dict)
async def get_user_current_profile(
    user_id: int,
    db=Depends(get_db),
    operator: dict = Depends(get_current_operator),
):
    """Obtener perfil QoS actual del usuario"""
    async with db.execute(
        "SELECT profile FROM users WHERE id = ?", (user_id,)
    ) as cursor:
        row = await cursor.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    profile_name = row["profile"]

    async with db.execute(
        "SELECT * FROM bandwidth_profiles WHERE name = ?", (profile_name,)
    ) as cursor:
        profile = await cursor.fetchone()

    if not profile:
        raise HTTPException(status_code=404, detail="Perfil no configurado")

    return dict(profile)
