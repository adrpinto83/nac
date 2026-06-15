"""
auth.py — Endpoints de autenticación y JWT
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from datetime import datetime, timedelta
from typing import Optional
import aiosqlite
from jose import JWTError, jwt
from passlib.context import CryptContext

from models import get_db
from schemas import LoginRequest, TokenResponse

router = APIRouter()

# Configuración JWT
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 8

# Context para contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security scheme
security = HTTPBearer()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Crear JWT token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def verify_token(credentials: HTTPAuthCredentials = Depends(security)):
    """Verificar JWT token"""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        operator_id: int = payload.get("sub")
        if operator_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido",
            )
        return operator_id
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado o inválido",
        )

async def get_current_operator(operator_id: int = Depends(verify_token)):
    """Obtener operador actual"""
    db = await get_db()
    async with db.execute(
        "SELECT * FROM operators WHERE id = ? AND enabled = 1", (operator_id,)
    ) as cursor:
        operator = await cursor.fetchone()

    if not operator:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Operador no encontrado",
        )

    return dict(operator)

@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """Login y generación de JWT"""
    db = await get_db()

    # Buscar operador
    async with db.execute(
        "SELECT * FROM operators WHERE username = ? AND enabled = 1",
        (request.username,),
    ) as cursor:
        operator = await cursor.fetchone()

    if not operator:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña inválidos",
        )

    # Verificar contraseña
    if not pwd_context.verify(request.password, operator["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña inválidos",
        )

    # Crear token
    expires_delta = timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    access_token = create_access_token(
        data={"sub": operator["id"], "username": operator["username"], "role": operator["role"]},
        expires_delta=expires_delta,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": int(ACCESS_TOKEN_EXPIRE_HOURS * 3600),
    }

@router.get("/me")
async def get_current_user(operator: dict = Depends(get_current_operator)):
    """Obtener datos del operador actual"""
    return {
        "id": operator["id"],
        "username": operator["username"],
        "full_name": operator["full_name"],
        "role": operator["role"],
    }

@router.post("/logout")
async def logout(operator: dict = Depends(get_current_operator)):
    """Logout (en cliente se descarta el token)"""
    return {"message": "Sesión cerrada"}
