"""Devices management router."""

from fastapi import APIRouter, HTTPException, status, Header
from pydantic import BaseModel
from typing import Optional, List
from app.database import get_db
from app.security import decode_token

router = APIRouter(prefix="/devices", tags=["devices"])


class DeviceCreate(BaseModel):
    user_id: int
    mac_address: str
    hostname: str
    device_type: str = "unknown"
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    os_type: Optional[str] = None
    os_version: Optional[str] = None
    notes: Optional[str] = None


class DeviceUpdate(BaseModel):
    hostname: Optional[str] = None
    device_type: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    os_type: Optional[str] = None
    os_version: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class DeviceResponse(BaseModel):
    id: int
    user_id: int
    mac_address: str
    ip_address: Optional[str]
    hostname: str
    device_type: str
    manufacturer: Optional[str]
    model: Optional[str]
    serial_number: Optional[str]
    os_type: Optional[str]
    os_version: Optional[str]
    status: str
    last_seen: Optional[str]
    notes: Optional[str]
    created_at: Optional[str]


async def verify_token(authorization: str = None) -> dict:
    """Verify token and return user."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = authorization.split(" ")[1]
    payload = decode_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    return payload


@router.get("/", response_model=List[DeviceResponse])
async def list_devices(authorization: Optional[str] = Header(None)):
    """List all devices."""
    await verify_token(authorization)

    db = await get_db()
    cursor = await db.execute(
        """SELECT id, user_id, mac_address, ip_address, hostname, device_type, manufacturer, model,
                  serial_number, os_type, os_version, status, last_seen, notes, created_at
           FROM devices ORDER BY created_at DESC"""
    )
    devices = await cursor.fetchall()
    await db.close()

    return [
        DeviceResponse(
            id=d[0],
            user_id=d[1],
            mac_address=d[2],
            ip_address=d[3],
            hostname=d[4],
            device_type=d[5] or "unknown",
            manufacturer=d[6],
            model=d[7],
            serial_number=d[8],
            os_type=d[9],
            os_version=d[10],
            status=d[11],
            last_seen=d[12],
            notes=d[13],
            created_at=d[14]
        )
        for d in devices
    ]


@router.post("/", response_model=DeviceResponse)
async def register_device(device: DeviceCreate, authorization: Optional[str] = Header(None)):
    """Register new device for a user."""
    await verify_token(authorization)

    db = await get_db()

    # Check user exists
    cursor = await db.execute("SELECT id FROM users WHERE id = ?", (device.user_id,))
    if not await cursor.fetchone():
        await db.close()
        raise HTTPException(status_code=404, detail="User not found")

    try:
        cursor = await db.execute(
            """INSERT INTO devices
               (user_id, mac_address, hostname, device_type, manufacturer, model, serial_number,
                os_type, os_version, status, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (device.user_id, device.mac_address, device.hostname, device.device_type,
             device.manufacturer, device.model, device.serial_number, device.os_type,
             device.os_version, "online", device.notes)
        )
        await db.commit()
        device_id = cursor.lastrowid

        return DeviceResponse(
            id=device_id,
            user_id=device.user_id,
            mac_address=device.mac_address,
            ip_address=None,
            hostname=device.hostname,
            device_type=device.device_type,
            manufacturer=device.manufacturer,
            model=device.model,
            serial_number=device.serial_number,
            os_type=device.os_type,
            os_version=device.os_version,
            status="online",
            last_seen=None,
            notes=device.notes,
            created_at=None
        )
    except Exception as e:
        await db.close()
        raise HTTPException(status_code=400, detail=f"Device registration failed: {str(e)}")
    finally:
        await db.close()


@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(device_id: int, authorization: Optional[str] = Header(None)):
    """Get device details."""
    await verify_token(authorization)

    db = await get_db()
    cursor = await db.execute(
        """SELECT id, user_id, mac_address, ip_address, hostname, device_type, manufacturer, model,
                  serial_number, os_type, os_version, status, last_seen, notes, created_at
           FROM devices WHERE id = ?""",
        (device_id,)
    )
    device = await cursor.fetchone()
    await db.close()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    return DeviceResponse(
        id=device[0],
        user_id=device[1],
        mac_address=device[2],
        ip_address=device[3],
        hostname=device[4],
        device_type=device[5] or "unknown",
        manufacturer=device[6],
        model=device[7],
        serial_number=device[8],
        os_type=device[9],
        os_version=device[10],
        status=device[11],
        last_seen=device[12],
        notes=device[13],
        created_at=device[14]
    )


@router.put("/{device_id}", response_model=DeviceResponse)
async def update_device(device_id: int, update: DeviceUpdate, authorization: Optional[str] = Header(None)):
    """Update device information."""
    await verify_token(authorization)

    db = await get_db()

    # Check device exists
    cursor = await db.execute("SELECT id FROM devices WHERE id = ?", (device_id,))
    if not await cursor.fetchone():
        await db.close()
        raise HTTPException(status_code=404, detail="Device not found")

    # Build update query
    updates = []
    values = []

    if update.hostname is not None:
        updates.append("hostname = ?")
        values.append(update.hostname)
    if update.device_type is not None:
        updates.append("device_type = ?")
        values.append(update.device_type)
    if update.manufacturer is not None:
        updates.append("manufacturer = ?")
        values.append(update.manufacturer)
    if update.model is not None:
        updates.append("model = ?")
        values.append(update.model)
    if update.serial_number is not None:
        updates.append("serial_number = ?")
        values.append(update.serial_number)
    if update.os_type is not None:
        updates.append("os_type = ?")
        values.append(update.os_type)
    if update.os_version is not None:
        updates.append("os_version = ?")
        values.append(update.os_version)
    if update.status is not None:
        updates.append("status = ?")
        values.append(update.status)
    if update.notes is not None:
        updates.append("notes = ?")
        values.append(update.notes)

    if updates:
        updates.append("updated_at = CURRENT_TIMESTAMP")
        values.append(device_id)

        query = f"UPDATE devices SET {', '.join(updates)} WHERE id = ?"
        await db.execute(query, values)
        await db.commit()

    # Get updated device
    cursor = await db.execute(
        """SELECT id, user_id, mac_address, ip_address, hostname, device_type, manufacturer, model,
                  serial_number, os_type, os_version, status, last_seen, notes, created_at
           FROM devices WHERE id = ?""",
        (device_id,)
    )
    device = await cursor.fetchone()
    await db.close()

    return DeviceResponse(
        id=device[0],
        user_id=device[1],
        mac_address=device[2],
        ip_address=device[3],
        hostname=device[4],
        device_type=device[5] or "unknown",
        manufacturer=device[6],
        model=device[7],
        serial_number=device[8],
        os_type=device[9],
        os_version=device[10],
        status=device[11],
        last_seen=device[12],
        notes=device[13],
        created_at=device[14]
    )


@router.delete("/{device_id}")
async def delete_device(device_id: int, authorization: Optional[str] = Header(None)):
    """Delete device."""
    await verify_token(authorization)

    db = await get_db()
    await db.execute("DELETE FROM devices WHERE id = ?", (device_id,))
    await db.commit()
    await db.close()

    return {"message": "Device deleted successfully"}


@router.get("/user/{user_id}/devices", response_model=List[DeviceResponse])
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
        """SELECT id, user_id, mac_address, ip_address, hostname, device_type, manufacturer, model,
                  serial_number, os_type, os_version, status, last_seen, notes, created_at
           FROM devices WHERE user_id = ? ORDER BY created_at DESC""",
        (user_id,)
    )
    devices = await cursor.fetchall()
    await db.close()

    return [
        DeviceResponse(
            id=d[0],
            user_id=d[1],
            mac_address=d[2],
            ip_address=d[3],
            hostname=d[4],
            device_type=d[5] or "unknown",
            manufacturer=d[6],
            model=d[7],
            serial_number=d[8],
            os_type=d[9],
            os_version=d[10],
            status=d[11],
            last_seen=d[12],
            notes=d[13],
            created_at=d[14]
        )
        for d in devices
    ]


@router.get("/by-mac/{mac_address}", response_model=DeviceResponse)
async def get_device_by_mac(mac_address: str, authorization: Optional[str] = Header(None)):
    """Get device by MAC address."""
    await verify_token(authorization)

    db = await get_db()
    cursor = await db.execute(
        """SELECT id, user_id, mac_address, ip_address, hostname, device_type, manufacturer, model,
                  serial_number, os_type, os_version, status, last_seen, notes, created_at
           FROM devices WHERE mac_address = ?""",
        (mac_address,)
    )
    device = await cursor.fetchone()
    await db.close()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    return DeviceResponse(
        id=device[0],
        user_id=device[1],
        mac_address=device[2],
        ip_address=device[3],
        hostname=device[4],
        device_type=device[5] or "unknown",
        manufacturer=device[6],
        model=device[7],
        serial_number=device[8],
        os_type=device[9],
        os_version=device[10],
        status=device[11],
        last_seen=device[12],
        notes=device[13],
        created_at=device[14]
    )
