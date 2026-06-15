"""Router de dispositivos."""

from fastapi import APIRouter, HTTPException, status, Depends
from app.models import get_db, Database, DeviceModel, AuditLogModel
from app.schemas import DeviceCreate, DeviceUpdate, DeviceResponse, DeviceWithUserResponse, ARPDevice
from app.dependencies import get_current_user, require_admin, get_router_client
from app.services import DeviceService, UserService
from routeros.client import RouterOSClient

router = APIRouter(prefix="/devices", tags=["devices"])


@router.post("/register", response_model=DeviceResponse)
async def register_device(
    device: DeviceCreate,
    current_user: dict = Depends(require_admin),
    db: Database = Depends(get_db),
    router: RouterOSClient = Depends(get_router_client),
):
    """Registra nuevo dispositivo (usuario + dispositivo en router)."""
    device_model = DeviceModel(db)
    user_service = UserService(db)
    device_service = DeviceService(db, router)
    audit_model = AuditLogModel(db)

    # Verificar que el usuario existe
    user = await user_service.user_model.get_user_by_id(device.user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Crear dispositivo en BD
    device_id = await device_model.create_device(
        mac_address=device.mac_address,
        device_name=device.device_name,
        user_id=device.user_id,
        device_type=device.device_type,
        profile_id=device.profile_id,
        comment=device.comment,
    )

    # Registrar en router (whitelist + queue)
    try:
        await device_service.register_device_on_router(
            mac_address=device.mac_address,
            device_name=device.device_name,
            profile_id=device.profile_id,
        )
    except Exception as e:
        # Si falla, eliminar del BD
        await device_model.delete_device(device_id)
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
