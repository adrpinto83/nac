"""Mensajes / Consultas entre usuarios y administradores."""

from fastapi import APIRouter, HTTPException, Header, Query
from pydantic import BaseModel
from typing import Optional, List
from app.database import get_db
from app.security import decode_token

router = APIRouter(prefix="/messages", tags=["messages"])


class MessageCreate(BaseModel):
    subject: str
    body: str
    to_user_id: Optional[int] = None  # None = al admin (cualquier admin lo ve)


class ReplyCreate(BaseModel):
    reply_body: str


class MessageOut(BaseModel):
    id: int
    from_user_id: int
    from_user_name: Optional[str]
    from_username: Optional[str]
    to_user_id: Optional[int]
    to_user_name: Optional[str]
    subject: str
    body: str
    is_read: bool
    reply_body: Optional[str]
    reply_at: Optional[str]
    replied_by_name: Optional[str]
    created_at: str


async def _get_caller(authorization: Optional[str]) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="No autenticado")
    payload = decode_token(authorization.split(" ")[1])
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido")
    return payload


async def _resolve_user(db, username: str):
    cur = await db.execute(
        "SELECT id, full_name, role FROM users WHERE username = ?", (username,)
    )
    return await cur.fetchone()


def _row_to_msg(row) -> MessageOut:
    return MessageOut(
        id=row[0],
        from_user_id=row[1],
        from_user_name=row[2],
        from_username=row[3],
        to_user_id=row[4],
        to_user_name=row[5],
        subject=row[6],
        body=row[7],
        is_read=bool(row[8]),
        reply_body=row[9],
        reply_at=row[10],
        replied_by_name=row[11],
        created_at=row[12],
    )


_SELECT = """
    SELECT m.id,
           m.from_user_id,
           fu.full_name  AS from_name,
           fu.username   AS from_username,
           m.to_user_id,
           tu.full_name  AS to_name,
           m.subject,
           m.body,
           m.is_read,
           m.reply_body,
           m.reply_at,
           rb.full_name  AS replied_by_name,
           m.created_at
    FROM messages m
    LEFT JOIN users fu ON m.from_user_id = fu.id
    LEFT JOIN users tu ON m.to_user_id   = tu.id
    LEFT JOIN users rb ON m.replied_by   = rb.id
"""


@router.post("/", response_model=MessageOut)
async def send_message(body: MessageCreate, authorization: Optional[str] = Header(None)):
    """Enviar una consulta. Usuarios la mandan al admin; admins pueden mandarla a un usuario."""
    payload = await _get_caller(authorization)
    db = await get_db()
    caller = await _resolve_user(db, payload["sub"])
    if not caller:
        await db.close()
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    caller_id, _, caller_role = caller

    # Si no es admin, to_user_id debe ser None (va al admin)
    to_uid = body.to_user_id if caller_role == "admin" else None

    cur = await db.execute(
        """INSERT INTO messages (from_user_id, to_user_id, subject, body)
           VALUES (?, ?, ?, ?)""",
        (caller_id, to_uid, body.subject.strip(), body.body.strip()),
    )
    await db.commit()
    msg_id = cur.lastrowid
    await db.close()

    db = await get_db()
    cur = await db.execute(f"{_SELECT} WHERE m.id = ?", (msg_id,))
    row = await cur.fetchone()
    await db.close()
    return _row_to_msg(row)


@router.get("/", response_model=List[MessageOut])
async def list_messages(authorization: Optional[str] = Header(None)):
    """
    Admin: ve todos los mensajes.
    Usuario: ve solo sus mensajes enviados y los que le mandaron.
    """
    payload = await _get_caller(authorization)
    db = await get_db()
    caller = await _resolve_user(db, payload["sub"])
    if not caller:
        await db.close()
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    caller_id, _, caller_role = caller

    if caller_role == "admin":
        cur = await db.execute(f"{_SELECT} ORDER BY m.created_at DESC")
    else:
        cur = await db.execute(
            f"{_SELECT} WHERE m.from_user_id = ? OR m.to_user_id = ? ORDER BY m.created_at DESC",
            (caller_id, caller_id),
        )

    rows = await cur.fetchall()
    await db.close()
    return [_row_to_msg(r) for r in rows]


@router.get("/unread-count")
async def unread_count(authorization: Optional[str] = Header(None)):
    """Cantidad de mensajes no leídos para el usuario actual."""
    payload = await _get_caller(authorization)
    db = await get_db()
    caller = await _resolve_user(db, payload["sub"])
    if not caller:
        await db.close()
        return {"count": 0}
    caller_id, _, caller_role = caller

    if caller_role == "admin":
        # Admin: no leídos donde él es destinatario (to_user_id NULL = para admin)
        cur = await db.execute(
            "SELECT COUNT(*) FROM messages WHERE (to_user_id IS NULL OR to_user_id = ?) AND is_read = 0 AND from_user_id != ?",
            (caller_id, caller_id),
        )
    else:
        cur = await db.execute(
            "SELECT COUNT(*) FROM messages WHERE to_user_id = ? AND is_read = 0",
            (caller_id,),
        )
    row = await cur.fetchone()
    await db.close()
    return {"count": row[0] if row else 0}


@router.put("/{msg_id}/read")
async def mark_read(msg_id: int, authorization: Optional[str] = Header(None)):
    """Marcar mensaje como leído."""
    payload = await _get_caller(authorization)
    db = await get_db()
    caller = await _resolve_user(db, payload["sub"])
    if not caller:
        await db.close()
        raise HTTPException(status_code=404)
    caller_id, _, caller_role = caller

    await db.execute(
        "UPDATE messages SET is_read = 1 WHERE id = ? AND (to_user_id = ? OR (to_user_id IS NULL AND ? = 'admin'))",
        (msg_id, caller_id, caller_role),
    )
    await db.commit()
    await db.close()
    return {"ok": True}


@router.post("/{msg_id}/reply", response_model=MessageOut)
async def reply_message(msg_id: int, body: ReplyCreate, authorization: Optional[str] = Header(None)):
    """Responder a una consulta. Solo admins pueden responder mensajes dirigidos al admin."""
    payload = await _get_caller(authorization)
    db = await get_db()
    caller = await _resolve_user(db, payload["sub"])
    if not caller:
        await db.close()
        raise HTTPException(status_code=404)
    caller_id, _, caller_role = caller

    # Verificar que el mensaje existe y que el caller puede responderlo
    cur = await db.execute("SELECT id, to_user_id FROM messages WHERE id = ?", (msg_id,))
    msg = await cur.fetchone()
    if not msg:
        await db.close()
        raise HTTPException(status_code=404, detail="Mensaje no encontrado")

    # Admin puede responder cualquier mensaje; usuario solo los que le llegaron a él
    if caller_role != "admin" and msg[1] != caller_id:
        await db.close()
        raise HTTPException(status_code=403, detail="Sin permiso para responder")

    await db.execute(
        """UPDATE messages SET reply_body = ?, reply_at = CURRENT_TIMESTAMP,
           replied_by = ?, is_read = 1 WHERE id = ?""",
        (body.reply_body.strip(), caller_id, msg_id),
    )
    await db.commit()
    await db.close()

    db = await get_db()
    cur = await db.execute(f"{_SELECT} WHERE m.id = ?", (msg_id,))
    row = await cur.fetchone()
    await db.close()
    return _row_to_msg(row)


@router.delete("/{msg_id}")
async def delete_message(msg_id: int, authorization: Optional[str] = Header(None)):
    """Eliminar mensaje. Solo admins."""
    payload = await _get_caller(authorization)
    db = await get_db()
    caller = await _resolve_user(db, payload["sub"])
    if not caller or caller[2] != "admin":
        await db.close()
        raise HTTPException(status_code=403, detail="Solo administradores")
    await db.execute("DELETE FROM messages WHERE id = ?", (msg_id,))
    await db.commit()
    await db.close()
    return {"ok": True}
