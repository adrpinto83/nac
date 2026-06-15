"""
devices.py — Endpoints para gestión de dispositivos
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from models import get_db
from schemas import DeviceCreate, DeviceResponse
from routers.auth import get_current_operator
from services import log_audit

router = APIRouter()

@router.post("/", response_model=dict)
async def create_device(
    device: DeviceCreate,
    db=Depends(get_db),
    operator: dict = Depends(get_current_operator),
):
    """Agregar dispositivo adicional a un usuario"""
    if operator["role"] not in ["SUPERADMIN", "ADMIN_RED"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permiso denegado",
        )

    # Verificar que el usuario existe
    async with db.execute("SELECT id FROM users WHERE id = ?", (device.user_id,)) as cursor:
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Verificar que la MAC no exista
    async with db.execute(
        "SELECT id FROM devices WHERE mac_address = ?", (device.mac_address,)
    ) as cursor:
        if await cursor.fetchone():
            raise HTTPException(status_code=400, detail="MAC ya registrada")

    # Insertar
    cursor = await db.execute(
        """INSERT INTO devices (user_id, mac_address, device_name, device_type)
        VALUES (?, ?, ?, ?)""",
        (device.user_id, device.mac_address, device.device_name, device.device_type),
    )
    device_id = cursor.lastrowid
    await db.commit()

    # Log
    await log_audit(db, operator["id"], "CREATE_DEVICE", "device", device_id)

    return {"id": device_id, "message": "Dispositivo agregado"}

@router.get("/user/{user_id}", response_model=List[dict])
async def get_user_devices(
    user_id: int,
    db=Depends(get_db),
    operator: dict = Depends(get_current_operator),
):
    """Listar dispositivos de un usuario"""
    async with db.execute(
        "SELECT * FROM devices WHERE user_id = ?", (user_id,)
    ) as cursor:
        devices = [dict(row) for row in await cursor.fetchall()]

    return devices

@router.delete("/{device_id}")
async def delete_device(
    device_id: int,
    db=Depends(get_db),
    operator: dict = Depends(get_current_operator),
):
    """Eliminar dispositivo"""
    if operator["role"] not in ["SUPERADMIN", "ADMIN_RED"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permiso denegado",
        )

    await db.execute("DELETE FROM devices WHERE id = ?", (device_id,))
    await db.commit()

    await log_audit(db, operator["id"], "DELETE_DEVICE", "device", device_id)

    return {"message": "Dispositivo eliminado"}
