"""Endpoints para bloqueo de sitios por usuario."""

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional, List
from app.database import get_db
from app.security import decode_token

router = APIRouter(prefix="/blocks", tags=["blocks"])


class BlockCreate(BaseModel):
    domain: str


async def verify_admin(authorization: Optional[str]):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="No autenticado")
    payload = decode_token(authorization.split(" ")[1])
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido")

    db = await get_db()
    try:
        cur = await db.execute(
            "SELECT id, role FROM users WHERE username = ?", (payload.get("sub"),)
        )
        caller = await cur.fetchone()
        if not caller or caller[1] != "admin":
            raise HTTPException(status_code=403, detail="Solo administradores")
        return {"caller_id": caller[0]}
    finally:
        await db.close()


def _clean_domain(domain: str) -> str:
    """Normaliza dominio: quita protocolo y rutas, devuelve solo el host."""
    d = domain.strip().lower()
    for prefix in ("https://", "http://", "www."):
        if d.startswith(prefix):
            d = d[len(prefix):]
    return d.split("/")[0].split("?")[0]


@router.get("/user/{user_id}", response_model=List[dict])
async def list_user_blocks(user_id: int, authorization: Optional[str] = Header(None)):
    """Lista los bloqueos activos de un usuario."""
    await verify_admin(authorization)

    db = await get_db()
    try:
        cur = await db.execute(
            "SELECT id, domain, created_at FROM user_site_blocks WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,),
        )
        rows = await cur.fetchall()
        return [{"id": r[0], "domain": r[1], "created_at": r[2]} for r in rows]
    finally:
        await db.close()


@router.post("/user/{user_id}", response_model=dict)
async def add_user_block(
    user_id: int,
    body: BlockCreate,
    authorization: Optional[str] = Header(None),
):
    """Agrega un bloqueo de dominio para un usuario."""
    caller = await verify_admin(authorization)
    domain = _clean_domain(body.domain)

    if not domain or "." not in domain:
        raise HTTPException(status_code=400, detail="Dominio inválido")

    db = await get_db()
    try:
        # Verificar que el usuario existe
        cur = await db.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        if not await cur.fetchone():
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        try:
            cur = await db.execute(
                "INSERT INTO user_site_blocks (user_id, domain, created_by) VALUES (?, ?, ?)",
                (user_id, domain, caller["caller_id"]),
            )
            block_id = cur.lastrowid
            await db.commit()
        except Exception:
            raise HTTPException(status_code=400, detail="El dominio ya está bloqueado para este usuario")

        # Intentar sincronizar con MikroTik (DNS estático)
        router_msg = ""
        try:
            from app.services.mikrotik_client import MikroTikClient
            client = MikroTikClient()
            await client.add_dns_block(domain, comment=f"user-block-{user_id}")
            router_msg = " y sincronizado con el router"
        except Exception as e:
            router_msg = f" (router no disponible: {e})"

        return {"id": block_id, "domain": domain, "message": f"Bloqueo agregado{router_msg}"}
    finally:
        await db.close()


@router.delete("/{block_id}", response_model=dict)
async def remove_user_block(block_id: int, authorization: Optional[str] = Header(None)):
    """Elimina un bloqueo de dominio."""
    await verify_admin(authorization)

    db = await get_db()
    try:
        cur = await db.execute(
            "SELECT id, user_id, domain FROM user_site_blocks WHERE id = ?", (block_id,)
        )
        row = await cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Bloqueo no encontrado")

        _, user_id, domain = row

        await db.execute("DELETE FROM user_site_blocks WHERE id = ?", (block_id,))
        await db.commit()

        # Intentar remover del router solo si no hay otros usuarios con el mismo dominio bloqueado
        cur = await db.execute(
            "SELECT COUNT(*) FROM user_site_blocks WHERE domain = ?", (domain,)
        )
        remaining = (await cur.fetchone())[0]

        router_msg = ""
        if remaining == 0:
            try:
                from app.services.mikrotik_client import MikroTikClient
                client = MikroTikClient()
                await client.remove_dns_block(domain, comment_filter=f"user-block-")
                router_msg = " y removido del router"
            except Exception as e:
                router_msg = f" (router no disponible: {e})"

        return {"message": f"Bloqueo eliminado{router_msg}"}
    finally:
        await db.close()
