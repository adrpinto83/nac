"""
dns.py — Endpoints para gestión de filtrado DNS
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from models import get_db
from schemas import DNSCategoryResponse, DNSEntryCreate
from routers.auth import get_current_operator
from services import log_audit, add_dns_entry_to_category, update_user_dns_categories

router = APIRouter()

@router.get("/categories", response_model=List[dict])
async def get_dns_categories(
    db=Depends(get_db),
    operator: dict = Depends(get_current_operator),
):
    """Listar categorías de DNS"""
    async with db.execute(
        "SELECT * FROM dns_categories WHERE enabled = 1"
    ) as cursor:
        categories = [dict(row) for row in await cursor.fetchall()]

    return categories

@router.get("/entries/{category_id}", response_model=List[dict])
async def get_dns_entries_by_category(
    category_id: int,
    db=Depends(get_db),
    operator: dict = Depends(get_current_operator),
):
    """Listar dominios de una categoría"""
    async with db.execute(
        "SELECT * FROM dns_entries WHERE category_id = ? AND enabled = 1",
        (category_id,),
    ) as cursor:
        entries = [dict(row) for row in await cursor.fetchall()]

    return entries

@router.post("/entries", response_model=dict)
async def create_dns_entry(
    entry: DNSEntryCreate,
    db=Depends(get_db),
    operator: dict = Depends(get_current_operator),
):
    """Agregar dominio a categoría"""
    if operator["role"] not in ["SUPERADMIN", "ADMIN_RED"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permiso denegado",
        )

    from services import routeros
    success, message = await add_dns_entry_to_category(db, entry.category_id, entry.domain)

    if not success:
        raise HTTPException(status_code=400, detail=message)

    await log_audit(
        db, operator["id"], "CREATE_DNS_ENTRY", "dns_entry",
        details=f"Domain: {entry.domain}, Category: {entry.category_id}"
    )

    return {"message": message}

@router.delete("/entries/{entry_id}")
async def delete_dns_entry(
    entry_id: int,
    db=Depends(get_db),
    operator: dict = Depends(get_current_operator),
):
    """Eliminar entrada DNS"""
    if operator["role"] not in ["SUPERADMIN", "ADMIN_RED"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permiso denegado",
        )

    # Obtener el dominio
    async with db.execute(
        "SELECT domain FROM dns_entries WHERE id = ?", (entry_id,)
    ) as cursor:
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Entrada no encontrada")
        domain = row["domain"]

    # Eliminar de BD
    await db.execute("DELETE FROM dns_entries WHERE id = ?", (entry_id,))
    await db.commit()

    # Eliminar de RouterOS
    from services import routeros
    await routeros.remove_dns_entry(domain)

    await log_audit(db, operator["id"], "DELETE_DNS_ENTRY", "dns_entry", entry_id)

    return {"message": "Entrada DNS eliminada"}

@router.get("/user/{user_id}/categories", response_model=List[dict])
async def get_user_dns_categories(
    user_id: int,
    db=Depends(get_db),
    operator: dict = Depends(get_current_operator),
):
    """Obtener categorías DNS habilitadas para un usuario"""
    async with db.execute(
        """SELECT dc.* FROM dns_categories dc
        JOIN user_dns_categories udc ON dc.id = udc.category_id
        WHERE udc.user_id = ? AND udc.enabled = 1""",
        (user_id,),
    ) as cursor:
        categories = [dict(row) for row in await cursor.fetchall()]

    return categories

@router.put("/user/{user_id}/categories", response_model=dict)
async def set_user_dns_categories(
    user_id: int,
    category_ids: List[int],
    db=Depends(get_db),
    operator: dict = Depends(get_current_operator),
):
    """Actualizar categorías DNS bloqueadas para un usuario"""
    if operator["role"] not in ["SUPERADMIN", "ADMIN_RED"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permiso denegado",
        )

    success, message = await update_user_dns_categories(db, user_id, category_ids)

    if not success:
        raise HTTPException(status_code=400, detail=message)

    await log_audit(
        db, operator["id"], "UPDATE_USER_DNS", "user", user_id,
        details=f"Categories: {category_ids}"
    )

    return {"message": message}
