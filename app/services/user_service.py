"""Servicio de usuarios."""

from typing import Optional, List
from app.models import Database, UserModel, DeviceModel
from app.auth import hash_password


class UserService:
    """Servicio de lógica de usuarios."""

    def __init__(self, db: Database):
        self.db = db
        self.user_model = UserModel(db)
        self.device_model = DeviceModel(db)

    async def create_user_with_device(
        self,
        username: str,
        password: str,
        full_name: str,
        mac_address: str,
        device_name: str,
        cedula: Optional[str] = None,
        cargo: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        profile_id: Optional[int] = None,
        device_type: Optional[str] = None,
    ) -> Optional[dict]:
        """Crea usuario + dispositivo (flujo de registro)."""
        # Crear usuario
        password_hash = hash_password(password)
        user_id = await self.user_model.create_user(
            username=username,
            password_hash=password_hash,
            full_name=full_name,
            cedula=cedula,
            cargo=cargo,
            email=email,
            phone=phone,
            role="user",
        )

        # Crear dispositivo
        device_id = await self.device_model.create_device(
            mac_address=mac_address,
            device_name=device_name,
            user_id=user_id,
            device_type=device_type,
            profile_id=profile_id,
        )

        return {
            "user_id": user_id,
            "device_id": device_id,
            "username": username,
            "full_name": full_name,
            "mac_address": mac_address,
        }

    async def get_user_with_devices(self, user_id: int) -> Optional[dict]:
        """Obtiene usuario con sus dispositivos."""
        user = await self.user_model.get_user_by_id(user_id)
        if not user:
            return None

        devices = await self.device_model.get_devices_by_user(user_id)

        return {**user, "devices": devices}

    async def suspend_user(self, user_id: int) -> bool:
        """Suspende usuario y sus dispositivos."""
        # Marcar usuario como suspendido
        await self.user_model.suspend_user(user_id)

        # Suspender dispositivos
        devices = await self.device_model.get_devices_by_user(user_id)
        for device in devices:
            await self.device_model.suspend_device(device["id"])

        return True

    async def delete_user_and_devices(self, user_id: int) -> bool:
        """Elimina usuario y sus dispositivos."""
        devices = await self.device_model.get_devices_by_user(user_id)
        for device in devices:
            await self.device_model.delete_device(device["id"])

        await self.user_model.delete_user(user_id)
        return True

    async def check_expiring_users(self, days: int = 7) -> List[dict]:
        """Obtiene usuarios que expiran pronto."""
        return await self.user_model.check_expired_users()

    async def expire_user(self, user_id: int) -> bool:
        """Marca usuario como expirado."""
        await self.user_model.mark_user_expired(user_id)

        # Suspender dispositivos
        devices = await self.device_model.get_devices_by_user(user_id)
        for device in devices:
            await self.device_model.mark_expired(device["id"])

        return True
