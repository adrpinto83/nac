"""Router de DNS."""

from fastapi import APIRouter, HTTPException, status, Depends
from app.models import get_db, Database, AuditLogModel
from app.schemas import DNSCategoryCreate, DNSCategoryResponse, DNSEntryCreate, DNSEntryResponse
from app.dependencies import get_current_user, require_admin, get_router_client
from routeros.client import RouterOSClient
from app.models.dns_entry import DNSCategoryModel, DNSEntryModel

router = APIRouter(prefix="/dns", tags=["dns"])


@router.post("/categories", response_model=DNSCategoryResponse)
async def create_category(
    category: DNSCategoryCreate,
    current_user: dict = Depends(require_admin),
    db: Database = Depends(get_db),
):
    """Crea categoría DNS."""
    model = DNSCategoryModel(db)
    category_id = await model.create_category(name=category.name, description=category.description)
    result = await model.get_category(category_id)
    return DNSCategoryResponse(**result)


@router.get("/categories", response_model=list[DNSCategoryResponse])
async def list_categories(current_user: dict = Depends(get_current_user), db: Database = Depends(get_db)):
    """Lista categorías DNS."""
    model = DNSCategoryModel(db)
    categories = await model.list_categories()
    return [DNSCategoryResponse(**c) for c in categories]


@router.post("/entries", response_model=DNSEntryResponse)
async def create_entry(
    entry: DNSEntryCreate,
    current_user: dict = Depends(require_admin),
    db: Database = Depends(get_db),
    router: RouterOSClient = Depends(get_router_client),
):
    """Crea entrada DNS bloqueada."""
    model = DNSEntryModel(db)

    # Verificar si ya existe
    if await model.domain_exists(entry.domain):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Domain already blocked")

    # Agregar en router
    try:
        await router.add_dns_entry(entry.domain, "0.0.0.0", comment=entry.comment)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    # Crear en BD
    entry_id = await model.create_entry(domain=entry.domain, category_id=entry.category_id, comment=entry.comment)

    # Log
    audit = AuditLogModel(db)
    await audit.log_action(
        operator_id=current_user["user_id"],
        action="add_dns_block",
        entity_type="dns",
        entity_id=entry.domain,
    )

    result = await model.get_entry(entry_id)
    return DNSEntryResponse(**result)


@router.get("/entries", response_model=list[DNSEntryResponse])
async def list_entries(
    category_id: int = None,
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db),
):
    """Lista entradas DNS."""
    model = DNSEntryModel(db)
    entries = await model.list_entries(category_id=category_id)
    return [DNSEntryResponse(**e) for e in entries]


@router.delete("/entries/{entry_id}")
async def delete_entry(
    entry_id: int,
    current_user: dict = Depends(require_admin),
    db: Database = Depends(get_db),
    router: RouterOSClient = Depends(get_router_client),
):
    """Elimina entrada DNS."""
    model = DNSEntryModel(db)
    entry = await model.get_entry(entry_id)
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found")

    # Eliminar del router
    try:
        await router.delete_dns_entry(entry["id"])
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    # Eliminar de BD
    await model.delete_entry(entry_id)

    # Log
    audit = AuditLogModel(db)
    await audit.log_action(
        operator_id=current_user["user_id"],
        action="remove_dns_block",
        entity_type="dns",
        entity_id=entry["domain"],
    )

    return {"message": "Entry deleted"}
