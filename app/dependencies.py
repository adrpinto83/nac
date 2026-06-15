"""Inyección de dependencias para FastAPI."""

from typing import Optional, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from app.models import Database, get_db
from app.auth import verify_token
from routeros.client import RouterOSClient
from app.config import get_settings

security = HTTPBearer()


async def get_current_user(credentials: Any = Depends(security)) -> dict:
    """Obtiene usuario actual del JWT token."""
    token = credentials.credentials
    payload = verify_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    return {"user_id": int(user_id), "username": payload.get("username"), "role": payload.get("role")}


async def get_router_client() -> RouterOSClient:
    """Obtiene cliente RouterOS."""
    settings = get_settings()
    async with RouterOSClient(
        host=settings.ROUTER_IP,
        port=settings.ROUTER_PORT,
        username=settings.ROUTER_USER,
        password=settings.ROUTER_PASSWORD,
        verify_ssl=settings.ROUTER_VERIFY_SSL,
    ) as client:
        yield client


def require_role(*required_roles: str):
    """Dependencia para requerir ciertos roles."""
    async def role_checker(current_user: dict = Depends(get_current_user)) -> dict:
        user_role = current_user.get("role")
        if user_role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return role_checker


require_admin = require_role("SUPERADMIN", "ADMIN_RED")
require_superadmin = require_role("SUPERADMIN")
