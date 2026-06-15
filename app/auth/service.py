"""Servicio de autenticación."""

from typing import Optional
from app.models import Database, UserModel, OperatorModel
from .security import hash_password, verify_password, create_access_token


class AuthService:
    """Servicio de autenticación."""

    def __init__(self, db: Database):
        self.db = db
        self.user_model = UserModel(db)
        self.operator_model = OperatorModel(db)

    async def register_user(
        self,
        username: str,
        password: str,
        full_name: str,
        cedula: Optional[str] = None,
        cargo: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
    ) -> Optional[dict]:
        """Registra nuevo usuario."""
        # Verificar si ya existe
        existing = await self.user_model.get_user_by_username(username)
        if existing:
            return None

        # Hash password
        password_hash = hash_password(password)

        # Crear usuario
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

        return await self.user_model.get_user_by_id(user_id)

    async def authenticate_user(self, username: str, password: str) -> Optional[dict]:
        """Autentica usuario."""
        user = await self.user_model.get_user_by_username(username)
        if not user:
            return None

        if not verify_password(password, user["password_hash"]):
            return None

        return user

    async def authenticate_operator(self, username: str, password: str) -> Optional[dict]:
        """Autentica operador."""
        operator = await self.operator_model.get_operator_by_username(username)
        if not operator:
            return None

        if not operator["active"]:
            return None

        if not verify_password(password, operator["password_hash"]):
            return None

        # Actualizar last_login
        await self.operator_model.update_last_login(operator["id"])

        return operator

    async def create_operator(
        self,
        username: str,
        password: str,
        role: str,
        created_by: Optional[int] = None,
    ) -> Optional[dict]:
        """Crea nuevo operador (solo SUPERADMIN)."""
        existing = await self.operator_model.get_operator_by_username(username)
        if existing:
            return None

        password_hash = hash_password(password)
        operator_id = await self.operator_model.create_operator(
            username=username,
            password_hash=password_hash,
            role=role,
            created_by=created_by,
        )

        return await self.operator_model.get_operator_by_id(operator_id)

    def generate_token(self, user_id: int, username: str, role: str) -> str:
        """Genera JWT token."""
        return create_access_token(data={"sub": str(user_id), "username": username, "role": role})
