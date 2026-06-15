"""
users.py — Endpoints para gestión de usuarios
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from models import get_db
from schemas import UserCreate, UserUpdate, UserResponse
from routers.auth import get_current_operator
from services import create_user, update_user, delete_user, get_user_stats, log_audit, init_routeros_client

router = APIRouter()

@router.post("/", response_model=dict)
async def create_new_user(
    user: UserCreate,
    db=Depends(get_db),
    operator: dict = Depends(get_current_operator),
):
    """Crear nuevo usuario (requiere rol ADMIN_RED o superior)"""
    if operator["role"] not in ["SUPERADMIN", "ADMIN_RED"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permiso denegado",
        )

    # Inicializar cliente RouterOS si no está listo
    from services import routeros
    if routeros is None:
        await init_routeros_client()

    success, user_id, message = await create_user(
        db,
        full_name=user.full_name,
        cedula=user.cedula,
        mac_address=user.mac_address,
        profile=user.profile,
        cargo=user.cargo,
        email=user.email,
        phone=user.phone,
        asset_tag=user.asset_tag,
        device_type=user.device_type,
        expires_at=user.expires_at,
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    # Log de auditoría
    await log_audit(
        db,
        operator["id"],
        "CREATE_USER",
        resource_type="user",
        resource_id=user_id,
        details=f"Usuario: {user.full_name}, MAC: {user.mac_address}",
    )

    return {"id": user_id, "message": message}

@router.get("/", response_model=List[dict])
async def list_users(
    db=Depends(get_db),
    operator: dict = Depends(get_current_operator),
    status: str = None,
):
    """Listar usuarios (filtro opcional por estado)"""
    if operator["role"] == "SOPORTE":
        # SOPORTE solo ve lectura
        pass

    query = "SELECT * FROM users"
    params = []

    if status:
        query += " WHERE status = ?"
        params.append(status)

    async with db.execute(query, params) as cursor:
        users = [dict(row) for row in await cursor.fetchall()]

    return users

@router.get("/{user_id}", response_model=dict)
async def get_user(
    user_id: int,
    db=Depends(get_db),
    operator: dict = Depends(get_current_operator),
):
    """Obtener detalles de un usuario"""
    async with db.execute("SELECT * FROM users WHERE id = ?", (user_id,)) as cursor:
        user = await cursor.fetchone()

    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return dict(user)

@router.put("/{user_id}")
async def update_user_info(
    user_id: int,
    user_data: UserUpdate,
    db=Depends(get_db),
    operator: dict = Depends(get_current_operator),
):
    """Actualizar usuario"""
    if operator["role"] not in ["SUPERADMIN", "ADMIN_RED"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permiso denegado",
        )

    # Inicializar cliente RouterOS si no está listo
    from services import routeros
    if routeros is None:
        await init_routeros_client()

    # Filtrar campos None
    update_data = {k: v for k, v in user_data.dict().items() if v is not None}

    if not update_data:
        return {"message": "No hay cambios"}

    success, message = await update_user(db, user_id, **update_data)

    if not success:
        raise HTTPException(status_code=400, detail=message)

    # Log de auditoría
    await log_audit(
        db,
        operator["id"],
        "UPDATE_USER",
        resource_type="user",
        resource_id=user_id,
        details=str(update_data),
    )

    return {"message": message}

@router.delete("/{user_id}")
async def remove_user(
    user_id: int,
    db=Depends(get_db),
    operator: dict = Depends(get_current_operator),
):
    """Eliminar usuario"""
    if operator["role"] not in ["SUPERADMIN", "ADMIN_RED"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permiso denegado",
        )

    # Inicializar cliente RouterOS si no está listo
    from services import routeros
    if routeros is None:
        await init_routeros_client()

    success, message = await delete_user(db, user_id)

    if not success:
        raise HTTPException(status_code=400, detail=message)

    # Log de auditoría
    await log_audit(
        db,
        operator["id"],
        "DELETE_USER",
        resource_type="user",
        resource_id=user_id,
    )

    return {"message": message}

@router.get("/{user_id}/stats", response_model=dict)
async def get_user_stats_endpoint(
    user_id: int,
    db=Depends(get_db),
    operator: dict = Depends(get_current_operator),
):
    """Obtener estadísticas de un usuario"""
    from services import get_user_stats
    stats = await get_user_stats(db, user_id)

    if not stats:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return stats
