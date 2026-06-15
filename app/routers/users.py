"""Router de usuarios."""

from fastapi import APIRouter, HTTPException, status, Depends
from app.models import get_db, Database, UserModel
from app.schemas import UserCreate, UserUpdate, UserResponse, PaginationParams
from app.dependencies import get_current_user, require_admin
from app.services import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserResponse)
async def create_user(
    user: UserCreate,
    current_user: dict = Depends(require_admin),
    db: Database = Depends(get_db),
):
    """Crea nuevo usuario (requiere ADMIN_RED+)."""
    user_model = UserModel(db)

    # Verificar si ya existe
    existing = await user_model.get_user_by_username(user.username)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")

    from app.auth import hash_password
    user_id = await user_model.create_user(
        username=user.username,
        password_hash=hash_password(user.password),
        full_name=user.full_name,
        cedula=user.cedula,
        cargo=user.cargo,
        email=user.email,
        phone=user.phone,
        created_by=current_user["user_id"],
    )

    result = await user_model.get_user_by_id(user_id)
    return UserResponse(**result)


@router.get("/", response_model=list[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 50,
    status_filter: str = None,
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db),
):
    """Lista usuarios con paginación."""
    user_model = UserModel(db)
    users = await user_model.list_users(
        status=status_filter,
        limit=limit,
        offset=skip,
    )
    return [UserResponse(**u) for u in users]


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db),
):
    """Obtiene usuario por ID."""
    user_model = UserModel(db)
    user = await user_model.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserResponse(**user)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user: UserUpdate,
    current_user: dict = Depends(require_admin),
    db: Database = Depends(get_db),
):
    """Actualiza usuario."""
    user_model = UserModel(db)

    existing = await user_model.get_user_by_id(user_id)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    update_data = user.dict(exclude_unset=True)
    await user_model.update_user(user_id, **update_data)

    result = await user_model.get_user_by_id(user_id)
    return UserResponse(**result)


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    current_user: dict = Depends(require_admin),
    db: Database = Depends(get_db),
):
    """Elimina usuario."""
    user_model = UserModel(db)

    existing = await user_model.get_user_by_id(user_id)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    service = UserService(db)
    await service.delete_user_and_devices(user_id)

    return {"message": "User deleted"}


@router.post("/{user_id}/suspend")
async def suspend_user(
    user_id: int,
    current_user: dict = Depends(require_admin),
    db: Database = Depends(get_db),
):
    """Suspende usuario."""
    user_model = UserModel(db)
    existing = await user_model.get_user_by_id(user_id)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    service = UserService(db)
    await service.suspend_user(user_id)
    return {"message": "User suspended"}


@router.post("/{user_id}/activate")
async def activate_user(
    user_id: int,
    current_user: dict = Depends(require_admin),
    db: Database = Depends(get_db),
):
    """Activa usuario."""
    user_model = UserModel(db)
    await user_model.enable_user(user_id)
    return {"message": "User activated"}
