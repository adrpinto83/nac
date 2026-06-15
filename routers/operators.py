"""
operators.py — Endpoints para gestión de operadores
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from passlib.context import CryptContext

from models import get_db
from schemas import OperatorCreate, OperatorUpdate, OperatorResponse
from routers.auth import get_current_operator
from services import log_audit

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.post("/", response_model=dict)
async def create_operator(
    operator_data: OperatorCreate,
    db=Depends(get_db),
    operator: dict = Depends(get_current_operator),
):
    """Crear nuevo operador (solo SUPERADMIN)"""
    if operator["role"] != "SUPERADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo SUPERADMIN puede crear operadores",
        )

    # Verificar username único
    async with db.execute(
        "SELECT id FROM operators WHERE username = ?", (operator_data.username,)
    ) as cursor:
        if await cursor.fetchone():
            raise HTTPException(status_code=400, detail="Username ya existe")

    # Hash de contraseña
    password_hash = pwd_context.hash(operator_data.password)

    cursor = await db.execute(
        """INSERT INTO operators (username, password_hash, full_name, role)
        VALUES (?, ?, ?, ?)""",
        (operator_data.username, password_hash, operator_data.full_name, operator_data.role),
    )
    new_op_id = cursor.lastrowid
    await db.commit()

    await log_audit(
        db, operator["id"], "CREATE_OPERATOR", "operator", new_op_id,
        details=f"Username: {operator_data.username}, Role: {operator_data.role}"
    )

    return {"id": new_op_id, "message": "Operador creado"}

@router.get("/", response_model=List[dict])
async def list_operators(
    db=Depends(get_db),
    operator: dict = Depends(get_current_operator),
):
    """Listar operadores (solo SUPERADMIN)"""
    if operator["role"] != "SUPERADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permiso denegado",
        )

    async with db.execute("SELECT id, username, full_name, role, enabled FROM operators") as cursor:
        operators = [dict(row) for row in await cursor.fetchall()]

    return operators

@router.put("/{op_id}")
async def update_operator(
    op_id: int,
    op_data: OperatorUpdate,
    db=Depends(get_db),
    operator: dict = Depends(get_current_operator),
):
    """Actualizar operador"""
    if operator["role"] != "SUPERADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo SUPERADMIN puede modificar operadores",
        )

    update_dict = {k: v for k, v in op_data.dict().items() if v is not None}

    if not update_dict:
        return {"message": "No hay cambios"}

    set_clause = ", ".join([f"{k} = ?" for k in update_dict.keys()])
    await db.execute(
        f"UPDATE operators SET {set_clause} WHERE id = ?",
        (*update_dict.values(), op_id),
    )
    await db.commit()

    await log_audit(db, operator["id"], "UPDATE_OPERATOR", "operator", op_id)

    return {"message": "Operador actualizado"}

@router.delete("/{op_id}")
async def delete_operator(
    op_id: int,
    db=Depends(get_db),
    operator: dict = Depends(get_current_operator),
):
    """Eliminar operador"""
    if operator["role"] != "SUPERADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo SUPERADMIN puede eliminar operadores",
        )

    await db.execute("DELETE FROM operators WHERE id = ?", (op_id,))
    await db.commit()

    await log_audit(db, operator["id"], "DELETE_OPERATOR", "operator", op_id)

    return {"message": "Operador eliminado"}
