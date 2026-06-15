"""Router synchronization endpoints - Sync approved users with MikroTik firewall."""

from fastapi import APIRouter, HTTPException, status, Header
from typing import Optional, List
from pydantic import BaseModel
from app.database import get_db
from app.security import decode_token
from app.services.mikrotik_client import MikroTikClient

router = APIRouter(prefix="/router", tags=["router"])


class SyncRequest(BaseModel):
    """Request to sync approved users."""
    pass


class SyncResponse(BaseModel):
    """Response from sync operation."""
    status: str
    added: List[str] = []
    removed: List[str] = []
    errors: List[str] = []
    message: str


class WhitelistRequest(BaseModel):
    """Request to add/remove user from whitelist."""
    mac_address: str
    username: Optional[str] = None


@router.post("/sync-approved-users", response_model=SyncResponse)
async def sync_approved_users(authorization: Optional[str] = Header(None)):
    """
    Sync all approved users' MAC addresses with router firewall.
    Only admin can call this endpoint.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = authorization.split(" ")[1]
    payload = decode_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    username = payload.get("sub")
    db = await get_db()

    # Check admin role
    cursor = await db.execute(
        "SELECT role FROM users WHERE username = ?",
        (username,)
    )
    user = await cursor.fetchone()

    if not user or user[0] != "admin":
        await db.close()
        raise HTTPException(status_code=403, detail="Admin access required")

    # Get all approved users with their devices
    cursor = await db.execute("""
        SELECT d.mac_address, u.username
        FROM devices d
        JOIN users u ON d.user_id = u.id
        WHERE u.approval_status = 'approved' AND u.is_active = 1
    """)
    approved_devices = await cursor.fetchall()
    await db.close()

    approved_macs = [device[0] for device in approved_devices if device[0]]

    # Sync with router
    try:
        async with MikroTikClient() as client:
            result = await client.sync_approved_users(approved_macs)

        return SyncResponse(
            status="success",
            added=result.get("added", []),
            removed=result.get("removed", []),
            errors=result.get("errors", []),
            message=f"Synced {len(approved_macs)} approved devices"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Router sync failed: {str(e)}"
        )


@router.post("/whitelist-user")
async def whitelist_user(
    request: WhitelistRequest,
    authorization: Optional[str] = Header(None)
):
    """Add a user to the router's authenticated-users whitelist."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = authorization.split(" ")[1]
    payload = decode_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    username = payload.get("sub")
    db = await get_db()

    # Check admin role
    cursor = await db.execute(
        "SELECT role FROM users WHERE username = ?",
        (username,)
    )
    user = await cursor.fetchone()

    if not user or user[0] != "admin":
        await db.close()
        raise HTTPException(status_code=403, detail="Admin access required")

    await db.close()

    # Add to router whitelist
    try:
        async with MikroTikClient() as client:
            success = await client.add_authenticated_user(
                request.mac_address,
                request.username
            )

        if success:
            return {
                "status": "success",
                "message": f"MAC {request.mac_address} added to whitelist"
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to add MAC to router"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Router error: {str(e)}"
        )


@router.post("/remove-user")
async def remove_user(
    request: WhitelistRequest,
    authorization: Optional[str] = Header(None)
):
    """Remove a user from the router's authenticated-users whitelist."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = authorization.split(" ")[1]
    payload = decode_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    username = payload.get("sub")
    db = await get_db()

    # Check admin role
    cursor = await db.execute(
        "SELECT role FROM users WHERE username = ?",
        (username,)
    )
    user = await cursor.fetchone()

    if not user or user[0] != "admin":
        await db.close()
        raise HTTPException(status_code=403, detail="Admin access required")

    await db.close()

    # Remove from router whitelist
    try:
        async with MikroTikClient() as client:
            success = await client.remove_authenticated_user(request.mac_address)

        if success:
            return {
                "status": "success",
                "message": f"MAC {request.mac_address} removed from whitelist"
            }
        else:
            return {
                "status": "success",
                "message": f"MAC {request.mac_address} not found in whitelist"
            }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Router error: {str(e)}"
        )


@router.get("/authenticated-users")
async def get_authenticated_users(authorization: Optional[str] = Header(None)):
    """Get list of currently authenticated users from router."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = authorization.split(" ")[1]
    payload = decode_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    username = payload.get("sub")
    db = await get_db()

    # Check admin role
    cursor = await db.execute(
        "SELECT role FROM users WHERE username = ?",
        (username,)
    )
    user = await cursor.fetchone()

    if not user or user[0] != "admin":
        await db.close()
        raise HTTPException(status_code=403, detail="Admin access required")

    await db.close()

    # Get from router
    try:
        async with MikroTikClient() as client:
            address_lists = await client.get_address_lists()

        auth_users = [
            item for item in address_lists
            if item.get("list") == "authenticated-users"
        ]

        return {
            "status": "success",
            "count": len(auth_users),
            "users": auth_users
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Router error: {str(e)}"
        )
