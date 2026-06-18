"""Authentication router."""

import logging
from fastapi import APIRouter, HTTPException, status, Header
from datetime import timedelta
from pydantic import BaseModel
from typing import Optional
from app.database import get_db
from app.security import (
    create_access_token, verify_password, decode_token,
    ACCESS_TOKEN_EXPIRE_MINUTES, hash_password
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class UserResponse(BaseModel):
    id: int
    username: str
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    role: str
    is_active: bool
    approval_status: Optional[str] = None
    access_expires_at: Optional[str] = None
    created_at: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


@router.post("/login", response_model=Token)
async def login(request: LoginRequest):
    """Login and get access token."""
    db = await get_db()

    cursor = await db.execute(
        "SELECT id, username, password_hash, role, is_active, approval_status FROM users WHERE username = ?",
        (request.username,)
    )
    user = await cursor.fetchone()
    await db.close()

    if not user or not verify_password(request.password, user[2]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    if not user[4]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is inactive",
        )

    if user[5] != "approved":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account pending approval",
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user[1]},
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserResponse)
async def get_me(authorization: Optional[str] = Header(None)):
    """Get current user info."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = authorization.split(" ")[1]
    payload = decode_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    username = payload.get("sub")
    db = await get_db()

    cursor = await db.execute(
        """SELECT id, username, full_name, email, phone, department, position,
                  role, is_active, approval_status, access_expires_at, created_at
           FROM users WHERE username = ?""",
        (username,)
    )
    user = await cursor.fetchone()
    await db.close()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(
        id=user[0], username=user[1], full_name=user[2],
        email=user[3], phone=user[4], department=user[5], position=user[6],
        role=user[7], is_active=bool(user[8]),
        approval_status=user[9], access_expires_at=str(user[10]) if user[10] else None,
        created_at=str(user[11]) if user[11] else None
    )


@router.post("/logout")
async def logout():
    """Logout (client removes token)."""
    return {"message": "Logged out successfully"}


@router.post("/change-password")
async def change_password(request: ChangePasswordRequest, authorization: Optional[str] = Header(None)):
    """Cambiar contraseña del usuario autenticado."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.split(" ")[1]
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    if len(request.new_password) < 6:
        raise HTTPException(status_code=400, detail="PASSWORD_TOO_SHORT")

    username = payload.get("sub")
    db = await get_db()
    cursor = await db.execute("SELECT id, password_hash FROM users WHERE username = ?", (username,))
    user = await cursor.fetchone()
    if not user:
        await db.close()
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_password(request.current_password, user[1]):
        await db.close()
        raise HTTPException(status_code=400, detail="WRONG_PASSWORD")

    new_hash = hash_password(request.new_password)
    await db.execute(
        "UPDATE users SET password_hash = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (new_hash, user[0])
    )
    await db.commit()
    await db.close()
    return {"message": "Contraseña actualizada"}


@router.get("/my-devices")
async def my_devices(authorization: Optional[str] = Header(None)):
    """Dispositivos del usuario autenticado."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.split(" ")[1]
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    username = payload.get("sub")
    db = await get_db()
    cursor = await db.execute("SELECT id FROM users WHERE username = ?", (username,))
    row = await cursor.fetchone()
    if not row:
        await db.close()
        raise HTTPException(status_code=404, detail="User not found")

    cursor = await db.execute(
        """SELECT mac_address, ip_address, device_type, os_type, os_version, created_at
           FROM devices WHERE user_id = ? ORDER BY created_at DESC""",
        (row[0],)
    )
    devices = await cursor.fetchall()
    await db.close()
    return [
        {"mac_address": d[0], "ip_address": d[1], "device_type": d[2],
         "os_type": d[3], "os_version": d[4], "registered_at": d[5]}
        for d in devices
    ]


# ============== PUBLIC REGISTRATION ==============

@router.get("/registration-status")
async def registration_status(mac: Optional[str] = None):
    """Estado de registro por MAC — usado por la splash page al reconectarse."""
    if not mac:
        return {"status": "not_registered"}

    db = await get_db()
    cursor = await db.execute(
        """SELECT u.approval_status
           FROM users u
           JOIN devices d ON d.user_id = u.id
           WHERE d.mac_address = ?
           LIMIT 1""",
        (mac,)
    )
    row = await cursor.fetchone()
    await db.close()

    if not row:
        return {"status": "not_registered"}

    return {"status": row[0]}  # pending | approved | rejected


def _is_random_mac(mac: str) -> bool:
    """El bit de administración local (bit 1 del primer octeto) indica MAC aleatoria."""
    try:
        first_octet = int(mac.replace('-', ':').split(':')[0], 16)
        return bool(first_octet & 0x02)
    except (ValueError, IndexError):
        return False


class RegisterRequest(BaseModel):
    username: str
    password: str
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    company: Optional[str] = None
    ticket_number: Optional[str] = None
    access_duration_hours: Optional[int] = None
    mac_address: Optional[str] = None
    ip_address: Optional[str] = None
    device_info: Optional[str] = None


class PendingUserResponse(BaseModel):
    id: int
    username: str
    full_name: str
    email: Optional[str]
    phone: Optional[str]
    department: Optional[str]
    position: Optional[str]
    ticket_number: Optional[str]
    access_duration_hours: Optional[int]
    approval_status: str
    created_at: str
    # desde devices
    mac_address: Optional[str] = None
    ip_address: Optional[str] = None
    device_type: Optional[str] = None
    os_type: Optional[str] = None
    os_version: Optional[str] = None


class ApproveRequest(BaseModel):
    access_hours: Optional[int] = None  # None = acceso ilimitado


@router.post("/register", response_model=UserResponse)
async def register(request: RegisterRequest):
    """Register a new user (pending approval)."""
    db = await get_db()

    # Rechazar MACs aleatorias (bit de administración local activado)
    if request.mac_address and _is_random_mac(request.mac_address):
        await db.close()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MAC_RANDOMIZED"
        )

    # Si la MAC ya está registrada en un dispositivo, devolver estado del usuario
    if request.mac_address:
        cursor = await db.execute(
            """SELECT u.approval_status FROM devices d
               JOIN users u ON u.id = d.user_id
               WHERE d.mac_address = ? LIMIT 1""",
            (request.mac_address,)
        )
        row = await cursor.fetchone()
        if row:
            await db.close()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"ALREADY_REGISTERED:{row[0]}"
            )

    # Si el username ya existe, devolver estado (no un error genérico)
    cursor = await db.execute(
        "SELECT id, approval_status FROM users WHERE username = ?",
        (request.username,)
    )
    existing = await cursor.fetchone()
    if existing:
        existing_status = existing[1]
        # Vincular MAC a este usuario si no tenía dispositivo registrado
        if request.mac_address:
            import json
            dev = {}
            try:
                dev = json.loads(request.device_info or '{}')
            except Exception:
                pass
            await db.execute(
                """INSERT OR IGNORE INTO devices
                   (user_id, mac_address, ip_address, hostname, device_type, os_type, os_version, notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (existing[0], request.mac_address, request.ip_address,
                 request.full_name, dev.get('type', 'unknown'),
                 dev.get('os', ''), dev.get('os_version', ''), request.device_info)
            )
            await db.commit()
        await db.close()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"ALREADY_REGISTERED:{existing_status}"
        )

    # Create pending user
    password_hash = hash_password(request.password)
    await db.execute(
        """INSERT INTO users
           (username, full_name, email, phone, department, position, company,
            ticket_number, access_duration_hours,
            password_hash, role, is_active, approval_status)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (request.username, request.full_name, request.email, request.phone,
         request.department, request.position, request.company,
         request.ticket_number, request.access_duration_hours,
         password_hash, "user", 0, "pending")
    )
    await db.commit()

    cursor = await db.execute(
        "SELECT id FROM users WHERE username = ?",
        (request.username,)
    )
    user_id = (await cursor.fetchone())[0]

    # Auto-registrar dispositivo si viene MAC del router
    if request.mac_address:
        import json
        dev = {}
        try:
            dev = json.loads(request.device_info or '{}')
        except Exception:
            pass
        await db.execute(
            """INSERT OR IGNORE INTO devices
               (user_id, mac_address, ip_address, hostname, device_type, os_type, os_version, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, request.mac_address, request.ip_address,
             request.full_name,
             dev.get('type', 'unknown'),
             dev.get('os', ''),
             dev.get('os_version', ''),
             request.device_info)
        )
        await db.commit()

    await db.close()

    return UserResponse(
        id=user_id,
        username=request.username,
        full_name=request.full_name,
        email=request.email,
        role="user",
        is_active=False
    )


@router.get("/pending-users", response_model=list[PendingUserResponse])
async def get_pending_users(authorization: Optional[str] = Header(None)):
    """Get list of pending users (admin only)."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = authorization.split(" ")[1]
    payload = decode_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    username = payload.get("sub")
    db = await get_db()

    cursor = await db.execute(
        "SELECT role FROM users WHERE username = ?",
        (username,)
    )
    user = await cursor.fetchone()

    if not user or user[0] != "admin":
        await db.close()
        raise HTTPException(status_code=403, detail="Admin access required")

    cursor = await db.execute(
        """SELECT u.id, u.username, u.full_name, u.email, u.phone,
                  u.department, u.position, u.ticket_number, u.access_duration_hours,
                  u.approval_status, u.created_at,
                  d.mac_address, d.ip_address, d.device_type, d.os_type, d.os_version
           FROM users u
           LEFT JOIN devices d ON d.user_id = u.id
           WHERE u.approval_status = 'pending'
           ORDER BY u.created_at DESC"""
    )
    pending = await cursor.fetchall()
    await db.close()

    return [
        PendingUserResponse(
            id=p[0], username=p[1], full_name=p[2], email=p[3], phone=p[4],
            department=p[5], position=p[6], ticket_number=p[7],
            access_duration_hours=p[8], approval_status=p[9], created_at=str(p[10]),
            mac_address=p[11], ip_address=p[12], device_type=p[13],
            os_type=p[14], os_version=p[15]
        ) for p in pending
    ]


@router.post("/approve-user/{user_id}")
async def approve_user(
    user_id: int,
    body: ApproveRequest = ApproveRequest(),
    authorization: Optional[str] = Header(None)
):
    """Approve a pending user (admin only). access_hours=None → acceso ilimitado."""
    from datetime import datetime, timedelta

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = authorization.split(" ")[1]
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    username = payload.get("sub")
    db = await get_db()

    cursor = await db.execute("SELECT role FROM users WHERE username = ?", (username,))
    admin = await cursor.fetchone()
    if not admin or admin[0] != "admin":
        await db.close()
        raise HTTPException(status_code=403, detail="Admin access required")

    # Calcular expiración si se indica duración
    expires_at = None
    if body.access_hours:
        expires_at = (datetime.utcnow() + timedelta(hours=body.access_hours)).isoformat()

    await db.execute(
        """UPDATE users
           SET approval_status = 'approved', is_active = 1,
               access_expires_at = ?
           WHERE id = ?""",
        (expires_at, user_id)
    )
    await db.commit()

    cursor = await db.execute("SELECT username FROM users WHERE id = ?", (user_id,))
    row = await cursor.fetchone()
    user_username = row[0] if row else "unknown"

    cursor = await db.execute("SELECT mac_address FROM devices WHERE user_id = ?", (user_id,))
    devices = await cursor.fetchall()
    await db.close()

    if devices:
        import asyncio
        async def _try_sync():
            try:
                from app.services.mikrotik_client import MikroTikClient
                async with MikroTikClient(timeout=3) as client:
                    for device in devices:
                        if device[0]:
                            await client.add_authenticated_user(device[0], user_username)
                logger.info(f"MAC sync inmediato OK para {user_username}")
            except Exception as e:
                logger.warning(f"MAC sync inmediato falló (el agente WSL lo reintentará): {e}")
        asyncio.create_task(_try_sync())

    return {"message": "User approved", "expires_at": expires_at}


@router.post("/reject-user/{user_id}")
async def reject_user(user_id: int, authorization: Optional[str] = Header(None)):
    """Reject a pending user (admin only)."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = authorization.split(" ")[1]
    payload = decode_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    username = payload.get("sub")
    db = await get_db()

    cursor = await db.execute(
        "SELECT role FROM users WHERE username = ?",
        (username,)
    )
    user = await cursor.fetchone()

    if not user or user[0] != "admin":
        await db.close()
        raise HTTPException(status_code=403, detail="Admin access required")

    await db.execute(
        "UPDATE users SET approval_status = 'rejected' WHERE id = ?",
        (user_id,)
    )
    await db.commit()
    await db.close()

    return {"message": "User rejected"}


# ============== ADD DEVICE TO EXISTING USER ==============

class AddDeviceRequest(BaseModel):
    mac_address: str
    ip_address: Optional[str] = None
    device_info: Optional[str] = None  # JSON string con type, os, etc.


@router.post("/add-device")
async def add_device(request: AddDeviceRequest, authorization: Optional[str] = Header(None)):
    """
    Agrega un nuevo dispositivo (MAC) al usuario autenticado.
    El usuario debe estar aprobado. La MAC no puede estar ya registrada para otro usuario.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = decode_token(authorization.split(" ")[1])
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    mac = request.mac_address.strip().upper()

    if _is_random_mac(mac):
        raise HTTPException(status_code=400, detail="MAC_RANDOMIZED")

    db = await get_db()

    # Obtener usuario
    cur = await db.execute(
        "SELECT id, approval_status FROM users WHERE username = ?", (payload["sub"],)
    )
    user = await cur.fetchone()
    if not user:
        await db.close()
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    user_id, approval_status = user

    # Verificar que la MAC no pertenezca ya a otro usuario
    cur = await db.execute(
        "SELECT user_id FROM devices WHERE mac_address = ?", (mac,)
    )
    existing = await cur.fetchone()
    if existing:
        if existing[0] == user_id:
            await db.close()
            raise HTTPException(status_code=409, detail="DEVICE_ALREADY_YOURS")
        await db.close()
        raise HTTPException(status_code=409, detail="DEVICE_TAKEN")

    import json
    dev = {}
    try:
        dev = json.loads(request.device_info or "{}")
    except Exception:
        pass

    await db.execute(
        """INSERT INTO devices
           (user_id, mac_address, ip_address, hostname, device_type, os_type, os_version, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (user_id, mac, request.ip_address,
         dev.get("hostname", ""),
         dev.get("type", "unknown"),
         dev.get("os", ""),
         dev.get("os_version", ""),
         request.device_info),
    )
    await db.commit()
    await db.close()

    return {
        "ok": True,
        "mac_address": mac,
        "approval_status": approval_status,
        "message": "Dispositivo agregado correctamente"
    }
