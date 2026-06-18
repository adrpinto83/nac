"""Users management router."""

from fastapi import APIRouter, HTTPException, status, Header
from pydantic import BaseModel
from typing import Optional, List
from app.database import get_db
from app.security import hash_password, decode_token

router = APIRouter(prefix="/users", tags=["users"])


class DeviceInfo(BaseModel):
    id: int
    mac_address: str
    ip_address: Optional[str]
    hostname: Optional[str]
    device_type: str
    manufacturer: Optional[str]
    model: Optional[str]
    os_type: Optional[str]
    status: str
    last_seen: Optional[str]


class RoleUpdateRequest(BaseModel):
    role: str  # 'user' | 'admin'


class UserCreate(BaseModel):
    username: str
    password: str
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    company: Optional[str] = None
    role: str = "user"


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    company: Optional[str] = None
    role: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    username: str
    full_name: str
    email: Optional[str]
    phone: Optional[str]
    department: Optional[str]
    position: Optional[str]
    company: Optional[str]
    role: str
    is_active: bool
    approval_status: Optional[str] = None
    created_at: Optional[str]


class UserDetailResponse(UserResponse):
    devices: List[DeviceInfo]
    device_count: int
    last_login: Optional[str]


async def verify_token(authorization: str = None) -> dict:
    """Verify token and return user."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = authorization.split(" ")[1]
    payload = decode_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    return payload


@router.get("/", response_model=List[UserResponse])
async def list_users(authorization: Optional[str] = Header(None)):
    """List all users."""
    await verify_token(authorization)

    db = await get_db()
    cursor = await db.execute(
        """SELECT id, username, full_name, email, phone, department, position, company,
                  role, is_active, approval_status, created_at
           FROM users ORDER BY created_at DESC"""
    )
    users = await cursor.fetchall()
    await db.close()

    return [
        UserResponse(
            id=u[0], username=u[1], full_name=u[2], email=u[3],
            phone=u[4], department=u[5], position=u[6], company=u[7],
            role=u[8], is_active=bool(u[9]), approval_status=u[10], created_at=u[11]
        )
        for u in users
    ]


@router.post("/", response_model=UserResponse)
async def create_user(user: UserCreate, authorization: Optional[str] = Header(None)):
    """Create new user with detailed information."""
    await verify_token(authorization)

    password_hash = hash_password(user.password)
    db = await get_db()

    try:
        cursor = await db.execute(
            """INSERT INTO users
               (username, password_hash, full_name, email, phone, department, position, company, role)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (user.username, password_hash, user.full_name, user.email, user.phone,
             user.department, user.position, user.company, user.role)
        )
        await db.commit()
        user_id = cursor.lastrowid

        return UserResponse(
            id=user_id,
            username=user.username,
            full_name=user.full_name,
            email=user.email,
            phone=user.phone,
            department=user.department,
            position=user.position,
            company=user.company,
            role=user.role,
            is_active=True,
            created_at=None
        )
    except Exception as e:
        await db.close()
        raise HTTPException(status_code=400, detail=f"User creation failed: {str(e)}")
    finally:
        await db.close()


@router.get("/{user_id}", response_model=UserDetailResponse)
async def get_user_detail(user_id: int, authorization: Optional[str] = Header(None)):
    """Get user with all devices."""
    await verify_token(authorization)

    db = await get_db()
    cursor = await db.execute(
        """SELECT id, username, full_name, email, phone, department, position, company, role, is_active, created_at, last_login
           FROM users WHERE id = ?""",
        (user_id,)
    )
    user = await cursor.fetchone()
    await db.close()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get devices for this user
    db = await get_db()
    cursor = await db.execute(
        """SELECT id, mac_address, ip_address, hostname, device_type, manufacturer, model, os_type, status, last_seen
           FROM devices WHERE user_id = ? ORDER BY created_at DESC""",
        (user_id,)
    )
    devices = await cursor.fetchall()
    await db.close()

    device_list = [
        DeviceInfo(
            id=d[0],
            mac_address=d[1],
            ip_address=d[2],
            hostname=d[3],
            device_type=d[4] or "unknown",
            manufacturer=d[5],
            model=d[6],
            os_type=d[7],
            status=d[8],
            last_seen=d[9]
        )
        for d in devices
    ]

    return UserDetailResponse(
        id=user[0],
        username=user[1],
        full_name=user[2],
        email=user[3],
        phone=user[4],
        department=user[5],
        position=user[6],
        company=user[7],
        role=user[8],
        is_active=bool(user[9]),
        created_at=user[10],
        devices=device_list,
        device_count=len(device_list),
        last_login=user[11]
    )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, update: UserUpdate, authorization: Optional[str] = Header(None)):
    """Update user information."""
    await verify_token(authorization)

    db = await get_db()

    # Check user exists
    cursor = await db.execute("SELECT id FROM users WHERE id = ?", (user_id,))
    if not await cursor.fetchone():
        await db.close()
        raise HTTPException(status_code=404, detail="User not found")

    # Build update query
    updates = []
    values = []

    if update.full_name is not None:
        updates.append("full_name = ?")
        values.append(update.full_name)
    if update.email is not None:
        updates.append("email = ?")
        values.append(update.email)
    if update.phone is not None:
        updates.append("phone = ?")
        values.append(update.phone)
    if update.department is not None:
        updates.append("department = ?")
        values.append(update.department)
    if update.position is not None:
        updates.append("position = ?")
        values.append(update.position)
    if update.company is not None:
        updates.append("company = ?")
        values.append(update.company)
    if update.role is not None:
        updates.append("role = ?")
        values.append(update.role)

    if updates:
        updates.append("updated_at = CURRENT_TIMESTAMP")
        values.append(user_id)

        query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
        await db.execute(query, values)
        await db.commit()

    # Get updated user
    cursor = await db.execute(
        """SELECT id, username, full_name, email, phone, department, position, company, role, is_active, created_at
           FROM users WHERE id = ?""",
        (user_id,)
    )
    user = await cursor.fetchone()
    await db.close()

    return UserResponse(
        id=user[0],
        username=user[1],
        full_name=user[2],
        email=user[3],
        phone=user[4],
        department=user[5],
        position=user[6],
        company=user[7],
        role=user[8],
        is_active=bool(user[9]),
        created_at=user[10]
    )


@router.delete("/{user_id}")
async def delete_user(user_id: int, authorization: Optional[str] = Header(None)):
    """Delete user and all associated devices."""
    await verify_token(authorization)

    db = await get_db()
    await db.execute("DELETE FROM users WHERE id = ?", (user_id,))
    await db.commit()
    await db.close()

    return {"message": "User deleted successfully"}


class AccessRequest(BaseModel):
    action: str  # 'approve' | 'block' | 'reject'


@router.put("/{user_id}/access")
async def set_user_access(user_id: int, body: AccessRequest, authorization: Optional[str] = Header(None)):
    """Conceder o revocar acceso a internet. Solo admins."""
    payload = await verify_token(authorization)
    if body.action not in ("approve", "block", "reject"):
        raise HTTPException(status_code=400, detail="Acción inválida. Usa 'approve', 'block' o 'reject'.")

    db = await get_db()
    cursor = await db.execute("SELECT role FROM users WHERE username = ?", (payload.get("sub"),))
    caller = await cursor.fetchone()
    if not caller or caller[0] != "admin":
        await db.close()
        raise HTTPException(status_code=403, detail="Solo administradores pueden cambiar el acceso.")

    cursor = await db.execute("SELECT id, username FROM users WHERE id = ?", (user_id,))
    target = await cursor.fetchone()
    if not target:
        await db.close()
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    if target[1] == "admin":
        await db.close()
        raise HTTPException(status_code=400, detail="No se puede modificar el administrador principal.")

    if body.action == "approve":
        new_status, new_active = "approved", 1
    else:
        new_status, new_active = "rejected", 0

    await db.execute(
        "UPDATE users SET approval_status = ?, is_active = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (new_status, new_active, user_id),
    )
    await db.commit()
    await db.close()
    return {"message": "Acceso actualizado", "approval_status": new_status, "is_active": bool(new_active)}


@router.put("/{user_id}/role")
async def update_user_role(user_id: int, body: RoleUpdateRequest, authorization: Optional[str] = Header(None)):
    """Cambiar rol de un usuario. Solo el administrador principal (username='admin') puede hacerlo."""
    payload = await verify_token(authorization)
    caller_username = payload.get("sub")

    if body.role not in ("user", "admin"):
        raise HTTPException(status_code=400, detail="Rol inválido. Usa 'user' o 'admin'.")

    db = await get_db()
    # Verificar que el que llama es el superadmin
    cursor = await db.execute("SELECT username, role FROM users WHERE username = ?", (caller_username,))
    caller = await cursor.fetchone()
    if not caller or caller[0] != "admin" or caller[1] != "admin":
        await db.close()
        raise HTTPException(status_code=403, detail="Solo el administrador principal puede cambiar roles.")

    # No permitir cambiar el propio rol del superadmin
    cursor = await db.execute("SELECT username FROM users WHERE id = ?", (user_id,))
    target = await cursor.fetchone()
    if not target:
        await db.close()
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    if target[0] == "admin":
        await db.close()
        raise HTTPException(status_code=400, detail="No se puede cambiar el rol del administrador principal.")

    await db.execute(
        "UPDATE users SET role = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (body.role, user_id)
    )
    await db.commit()
    await db.close()
    return {"message": "Rol actualizado", "role": body.role}


@router.get("/{user_id}/devices", response_model=List[DeviceInfo])
async def get_user_devices(user_id: int, authorization: Optional[str] = Header(None)):
    """Get all devices for a specific user."""
    await verify_token(authorization)

    db = await get_db()

    # Check user exists
    cursor = await db.execute("SELECT id FROM users WHERE id = ?", (user_id,))
    if not await cursor.fetchone():
        await db.close()
        raise HTTPException(status_code=404, detail="User not found")

    # Get devices
    cursor = await db.execute(
        """SELECT id, mac_address, ip_address, hostname, device_type, manufacturer, model, os_type, status, last_seen
           FROM devices WHERE user_id = ? ORDER BY created_at DESC""",
        (user_id,)
    )
    devices = await cursor.fetchall()
    await db.close()

    return [
        DeviceInfo(
            id=d[0],
            mac_address=d[1],
            ip_address=d[2],
            hostname=d[3],
            device_type=d[4] or "unknown",
            manufacturer=d[5],
            model=d[6],
            os_type=d[7],
            status=d[8],
            last_seen=d[9]
        )
        for d in devices
    ]
