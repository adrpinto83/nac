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
    email: str
    role: str
    is_active: bool


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
        "SELECT id, username, full_name, email, role, is_active FROM users WHERE username = ?",
        (username,)
    )
    user = await cursor.fetchone()
    await db.close()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(
        id=user[0],
        username=user[1],
        full_name=user[2],
        email=user[3],
        role=user[4],
        is_active=bool(user[5])
    )


@router.post("/logout")
async def logout():
    """Logout (client removes token)."""
    return {"message": "Logged out successfully"}


# ============== PUBLIC REGISTRATION ==============

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
    mac_address: Optional[str] = None
    ip_address: Optional[str] = None
    device_info: Optional[str] = None


class PendingUserResponse(BaseModel):
    id: int
    username: str
    full_name: str
    email: Optional[str]
    phone: Optional[str]
    approval_status: str
    created_at: str


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

    # Check if user exists
    cursor = await db.execute(
        "SELECT id FROM users WHERE username = ?",
        (request.username,)
    )
    if await cursor.fetchone():
        await db.close()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )

    # Create pending user
    password_hash = hash_password(request.password)
    await db.execute(
        """INSERT INTO users
           (username, full_name, email, phone, company, password_hash, role, is_active, approval_status)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (request.username, request.full_name, request.email, request.phone,
         request.device_info, password_hash, "user", 0, "pending")
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
        "SELECT id, username, full_name, email, phone, approval_status, created_at FROM users WHERE approval_status = 'pending' ORDER BY created_at DESC"
    )
    pending = await cursor.fetchall()
    await db.close()

    return [
        PendingUserResponse(
            id=p[0],
            username=p[1],
            full_name=p[2],
            email=p[3],
            phone=p[4],
            approval_status=p[5],
            created_at=str(p[6])
        ) for p in pending
    ]


@router.post("/approve-user/{user_id}")
async def approve_user(user_id: int, authorization: Optional[str] = Header(None)):
    """Approve a pending user (admin only)."""
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
        "UPDATE users SET approval_status = 'approved', is_active = 1 WHERE id = ?",
        (user_id,)
    )
    await db.commit()

    # Get user's devices to whitelist them
    cursor = await db.execute(
        "SELECT username FROM users WHERE id = ?",
        (user_id,)
    )
    user_info = await cursor.fetchone()
    user_username = user_info[0] if user_info else "unknown"

    cursor = await db.execute(
        "SELECT mac_address FROM devices WHERE user_id = ?",
        (user_id,)
    )
    devices = await cursor.fetchall()
    await db.close()

    # Add devices to router whitelist (async, don't block)
    if devices:
        try:
            from app.services.mikrotik_client import MikroTikClient
            async with MikroTikClient() as client:
                for device in devices:
                    if device[0]:
                        await client.add_authenticated_user(device[0], user_username)
        except Exception as e:
            logger.warning(f"Could not sync MAC to router: {str(e)}")

    return {"message": "User approved"}


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
