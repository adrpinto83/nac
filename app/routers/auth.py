"""Authentication router."""

from fastapi import APIRouter, HTTPException, status, Header
from datetime import timedelta
from pydantic import BaseModel
from typing import Optional
from app.database import get_db
from app.security import (
    create_access_token, verify_password, decode_token,
    ACCESS_TOKEN_EXPIRE_MINUTES, hash_password
)

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
        "SELECT id, username, password_hash, role, is_active FROM users WHERE username = ?",
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
