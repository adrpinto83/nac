"""Devices management router."""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from app.database import get_db
from app.security import decode_token

router = APIRouter(prefix="/devices", tags=["devices"])


class DeviceCreate(BaseModel):
    mac_address: str
    hostname: str
    device_type: str = "unknown"


class DeviceResponse(BaseModel):
    id: int
    mac_address: str
    ip_address: str
    hostname: str
    status: str
    last_seen: str


async def verify_token(authorization: str = None) -> dict:
    """Verify token and return user."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = authorization.split(" ")[1]
    payload = decode_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    return payload


@router.get("/", response_model=list[DeviceResponse])
async def list_devices(authorization: str = None):
    """List all devices."""
    await verify_token(authorization)

    db = await get_db()
    cursor = await db.execute(
        "SELECT id, mac_address, ip_address, hostname, status, last_seen FROM devices"
    )
    devices = await cursor.fetchall()
    await db.close()

    return [
        DeviceResponse(
            id=d[0],
            mac_address=d[1],
            ip_address=d[2] or "",
            hostname=d[3],
            status=d[4],
            last_seen=d[5] or ""
        )
        for d in devices
    ]


@router.post("/", response_model=DeviceResponse)
async def register_device(device: DeviceCreate, authorization: str = None):
    """Register new device."""
    await verify_token(authorization)

    db = await get_db()

    try:
        cursor = await db.execute(
            "INSERT INTO devices (mac_address, hostname, status) VALUES (?, ?, ?)",
            (device.mac_address, device.hostname, "online")
        )
        await db.commit()
        device_id = cursor.lastrowid

        return DeviceResponse(
            id=device_id,
            mac_address=device.mac_address,
            ip_address="",
            hostname=device.hostname,
            status="online",
            last_seen=""
        )
    except Exception as e:
        await db.close()
        raise HTTPException(status_code=400, detail=f"Device registration failed: {str(e)}")
    finally:
        await db.close()


@router.get("/live", response_model=list[DeviceResponse])
async def get_live_devices(authorization: str = None):
    """Get live devices from router."""
    await verify_token(authorization)

    db = await get_db()
    cursor = await db.execute(
        "SELECT id, mac_address, ip_address, hostname, status, last_seen FROM devices WHERE status = 'online'"
    )
    devices = await cursor.fetchall()
    await db.close()

    return [
        DeviceResponse(
            id=d[0],
            mac_address=d[1],
            ip_address=d[2] or "",
            hostname=d[3],
            status=d[4],
            last_seen=d[5] or ""
        )
        for d in devices
    ]


@router.delete("/{device_id}")
async def delete_device(device_id: int, authorization: str = None):
    """Delete device."""
    await verify_token(authorization)

    db = await get_db()
    await db.execute("DELETE FROM devices WHERE id = ?", (device_id,))
    await db.commit()
    await db.close()

    return {"message": "Device deleted"}
