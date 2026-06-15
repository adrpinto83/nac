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
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Router error: {str(e)}")

    # Log auditoría
    await audit_model.log_action(
        operator_id=current_user["user_id"],
        action="register",
        entity_type="device",
        entity_id=str(device_id),
        entity_name=device.device_name,
        result="success",
    )

    result = await device_model.get_device_by_id(device_id)
    return DeviceResponse(**result)


@router.get("/", response_model=list[DeviceWithUserResponse])
async def list_devices(
    skip: int = 0,
    limit: int = 50,
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db),
):
    """Lista dispositivos."""
    device_model = DeviceModel(db)
    devices = await device_model.get_all_devices_with_info()
    return [DeviceWithUserResponse(**d) for d in devices[skip : skip + limit]]


@router.get("/live", response_model=list[ARPDevice])
async def get_live_devices(
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db),
    router: RouterOSClient = Depends(get_router_client),
):
    """Obtiene dispositivos vivos en la red (ARP)."""
    service = DeviceService(db, router)
    devices = await service.get_live_devices()
    return [ARPDevice(**d) for d in devices]


@router.post("/{device_id}/block")
async def block_device(
    device_id: int,
    current_user: dict = Depends(require_admin),
    db: Database = Depends(get_db),
    router: RouterOSClient = Depends(get_router_client),
):
    """Bloquea dispositivo."""
    device_model = DeviceModel(db)
    device = await device_model.get_device_by_id(device_id)
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    service = DeviceService(db, router)
    await service.block_device_on_router(device["mac_address"])
    await device_model.block_device(device_id)

    audit_model = AuditLogModel(db)
    await audit_model.log_action(
        operator_id=current_user["user_id"],
        action="block",
        entity_type="device",
        entity_id=str(device_id),
    )

    return {"message": "Device blocked"}


@router.post("/{device_id}/unblock")
async def unblock_device(
    device_id: int,
    current_user: dict = Depends(require_admin),
    db: Database = Depends(get_db),
    router: RouterOSClient = Depends(get_router_client),
):
    """Desbloquea dispositivo."""
    device_model = DeviceModel(db)
    device = await device_model.get_device_by_id(device_id)
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    service = DeviceService(db, router)
    await service.unblock_device_on_router(device["mac_address"])
    await device_model.unblock_device(device_id)

    audit_model = AuditLogModel(db)
    await audit_model.log_action(
        operator_id=current_user["user_id"],
        action="unblock",
        entity_type="device",
        entity_id=str(device_id),
    )

    return {"message": "Device unblocked"}


@router.delete("/{device_id}")
async def delete_device(
    device_id: int,
    current_user: dict = Depends(require_admin),
    db: Database = Depends(get_db),
    router: RouterOSClient = Depends(get_router_client),
):
    """Elimina dispositivo."""
    device_model = DeviceModel(db)
    device = await device_model.get_device_by_id(device_id)
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    service = DeviceService(db, router)
    await service.unregister_device_from_router(device["mac_address"])
    await device_model.delete_device(device_id)

    audit_model = AuditLogModel(db)
    await audit_model.log_action(
        operator_id=current_user["user_id"],
        action="delete",
        entity_type="device",
        entity_id=str(device_id),
    )

    return {"message": "Device deleted"}
