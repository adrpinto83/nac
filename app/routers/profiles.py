"""Router de perfiles QoS."""

from fastapi import APIRouter, HTTPException, status, Depends
from app.models import get_db, Database, ProfileModel
from app.schemas import ProfileCreate, ProfileUpdate, ProfileResponse
from app.dependencies import get_current_user, require_superadmin

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.post("/", response_model=ProfileResponse)
async def create_profile(
    profile: ProfileCreate,
    current_user: dict = Depends(require_superadmin),
    db: Database = Depends(get_db),
):
    """Crea perfil QoS (solo SUPERADMIN)."""
    model = ProfileModel(db)
    existing = await model.get_profile_by_name(profile.name)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Profile already exists")

    profile_id = await model.create_profile(
        name=profile.name,
        max_upload=profile.max_upload,
        max_download=profile.max_download,
        priority=profile.priority,
        description=profile.description,
    )

    result = await model.get_profile_by_id(profile_id)
    return ProfileResponse(**result)


@router.get("/", response_model=list[ProfileResponse])
async def list_profiles(current_user: dict = Depends(get_current_user), db: Database = Depends(get_db)):
    """Lista todos los perfiles."""
    model = ProfileModel(db)
    profiles = await model.list_profiles()
    return [ProfileResponse(**p) for p in profiles]


@router.put("/{profile_id}", response_model=ProfileResponse)
async def update_profile(
    profile_id: int,
    profile: ProfileUpdate,
    current_user: dict = Depends(require_superadmin),
    db: Database = Depends(get_db),
):
    """Actualiza perfil."""
    model = ProfileModel(db)
    existing = await model.get_profile_by_id(profile_id)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")

    await model.update_profile(
        profile_id,
        max_upload=profile.max_upload,
        max_download=profile.max_download,
        priority=profile.priority,
        description=profile.description,
    )

    result = await model.get_profile_by_id(profile_id)
    return ProfileResponse(**result)
