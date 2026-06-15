"""Router de autenticación."""

from fastapi import APIRouter, HTTPException, status, Depends
from app.models import get_db, Database
from app.auth import AuthService
from app.schemas import LoginRequest, TokenResponse, UserResponse, OperatorCreate, OperatorResponse
from app.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: Database = Depends(get_db)):
    """Login de usuario o operador."""
    auth_service = AuthService(db)

    # Intentar login de usuario
    user = await auth_service.authenticate_user(request.username, request.password)
    if user:
        token = auth_service.generate_token(user["id"], user["username"], user["role"])
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": UserResponse(**user),
        }

    # Intentar login de operador
    operator = await auth_service.authenticate_operator(request.username, request.password)
    if operator:
        token = auth_service.generate_token(operator["id"], operator["username"], operator["role"])
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": OperatorResponse(**operator),
        }

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user), db: Database = Depends(get_db)):
    """Obtiene información del usuario actual."""
    user_model = __import__("app.models", fromlist=["UserModel"]).UserModel(db)
    user = await user_model.get_user_by_id(current_user["user_id"])
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserResponse(**user)


@router.post("/logout")
async def logout():
    """Logout (el cliente elimina el token)."""
    return {"message": "Logged out successfully"}


@router.post("/operators", response_model=OperatorResponse)
async def create_operator(
    operator: OperatorCreate,
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db),
):
    """Crea nuevo operador (solo SUPERADMIN)."""
    if current_user.get("role") != "SUPERADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    auth_service = AuthService(db)
    new_operator = await auth_service.create_operator(
        username=operator.username,
        password=operator.password,
        role=operator.role,
        created_by=current_user["user_id"],
    )

    if not new_operator:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Operator already exists")

    return OperatorResponse(**new_operator)
