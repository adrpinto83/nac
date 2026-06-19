"""Router synchronization endpoints - Sync approved users with MikroTik hotspot."""

import os
from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Header, Query
from fastapi.responses import PlainTextResponse
from typing import Optional, List
from pydantic import BaseModel
from app.database import get_db
from app.security import decode_token
from app.services.mikrotik_client import MikroTikClient

# Clave compartida entre Railway y el router (configura NAC_SYNC_KEY en Railway env vars)
SYNC_KEY = os.environ.get("NAC_SYNC_KEY", "nac-sync-2024")

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


# ─── ENDPOINT PÚBLICO: el router lo descarga y ejecuta cada 60 s ─────────────

@router.get("/pull-script", response_class=PlainTextResponse)
async def pull_script(key: str = Query(default="")):
    """
    El router MikroTik descarga este script RouterOS y lo importa cada minuto.
    No requiere ningún PC corriendo.

    Sincroniza:
      - hotspot users (MAC como nombre, para auto-login)
      - forward filter accept rules (tráfico saliente)
      - bypass-established rule (tráfico de retorno)

    Protegido con NAC_SYNC_KEY.
    """
    if key != SYNC_KEY:
        raise HTTPException(status_code=403, detail="Invalid key")

    now = datetime.utcnow().isoformat()
    db = await get_db()
    cursor = await db.execute(
        """SELECT d.mac_address, u.download_mbps, u.upload_mbps
           FROM devices d
           JOIN users u ON d.user_id = u.id
           WHERE u.approval_status = 'approved'
             AND u.is_active = 1
             AND (u.access_expires_at IS NULL OR u.access_expires_at > ?)""",
        (now,)
    )
    rows = await cursor.fetchall()
    await db.close()

    # {MAC_UPPER: (download_mbps, upload_mbps)}
    devices: dict[str, tuple] = {}
    for mac, dl, ul in rows:
        if mac:
            devices[mac.upper()] = (dl, ul)

    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    macs_str = ", ".join(devices.keys()) if devices else "(ninguno)"

    lines = [
        f"# NAC-SYNC  {ts}  |  {len(devices)} dispositivos aprobados",
        f"# MACs: {macs_str}",
        "",
        "# ── Hotspot users ──────────────────────────────────────────────────",
    ]

    # Generar condición para remover usuarios que ya no están aprobados
    if devices:
        not_in = " and ".join(f'$name != "{mac}"' for mac in devices)
    else:
        not_in = "true"

    lines += [
        ":foreach u in=[/ip/hotspot/user find comment~\"NAC:\"] do={",
        "    :local name [/ip/hotspot/user get $u name]",
        f"    :if ({not_in}) do={{",
        "        /ip/hotspot/user remove $u",
        '        :log info ("NAC-SYNC: -user " . $name)',
        "    }",
        "}",
        "",
    ]

    for mac, (dl, ul) in devices.items():
        rate = ""
        if dl or ul:
            d = f"{dl}M" if dl else "0"
            u = f"{ul}M" if ul else "0"
            rate = f"{d}/{u}"
        rate_attr = f' rate-limit="{rate}"' if rate else ""
        lines += [
            f':if ([:len [/ip/hotspot/user find name="{mac}"]] = 0) do={{',
            f'    /ip/hotspot/user add name="{mac}" profile=default password="" comment="NAC:{mac}"{rate_attr}',
            f'    :log info "NAC-SYNC: +user {mac}"',
            "}",
        ]
        if rate:
            lines += [
                f'    :foreach u in=[/ip/hotspot/user find name="{mac}"] do={{',
                f'        :if ([/ip/hotspot/user get $u rate-limit] != "{rate}") do={{',
                f'            /ip/hotspot/user set $u rate-limit="{rate}"',
                f'            :log info "NAC-SYNC: ~rate {mac} {rate}"',
                "        }",
                "    }",
            ]

    lines += [
        "",
        "# ── Forward filter rules ────────────────────────────────────────────",
        ":local fwdId \"\"",
        ":foreach r in=[/ip/firewall/filter find chain=forward action=jump jump-target=hs-unauth dynamic=yes] do={",
        "    :set fwdId [/ip/firewall/filter get $r .id]",
        "}",
        "",
    ]

    if devices:
        fwd_not_in = " and ".join(
            f'[:toupper $mac] != "{mac}"' for mac in devices
        )
    else:
        fwd_not_in = "true"

    lines += [
        ":foreach r in=[/ip/firewall/filter find chain=forward comment~\"NAC:\" action=accept] do={",
        "    :local mac [/ip/firewall/filter get $r src-mac-address]",
        f"    :if ({fwd_not_in}) do={{",
        "        /ip/firewall/filter remove $r",
        '        :log info ("NAC-SYNC: -fwd " . $mac)',
        "    }",
        "}",
        "",
    ]

    for mac in devices:
        lines += [
            f':if ([:len [/ip/firewall/filter find chain=forward src-mac-address="{mac}" action=accept]] = 0) do={{',
            f'    :if ($fwdId != "") do={{',
            f'        /ip/firewall/filter add chain=forward src-mac-address="{mac}" action=accept comment="NAC:{mac}" place-before=$fwdId',
            f'    }} else={{',
            f'        /ip/firewall/filter add chain=forward src-mac-address="{mac}" action=accept comment="NAC:{mac}"',
            f'    }}',
            f'    :log info "NAC-SYNC: +fwd {mac}"',
            "}",
        ]

    lines += [
        "",
        "# ── Bypass established/related ──────────────────────────────────────",
        ':if ([:len [/ip/firewall/filter find chain=forward comment="bypass-established"]] = 0) do={',
        '    :if ($fwdId != "") do={',
        '        /ip/firewall/filter add chain=forward connection-state=established,related action=accept comment="bypass-established" place-before=$fwdId',
        '    } else={',
        '        /ip/firewall/filter add chain=forward connection-state=established,related action=accept comment="bypass-established"',
        '    }',
        '    :log info "NAC-SYNC: +bypass-established"',
        "}",
        "",
        ':log info "NAC-SYNC: completo"',
    ]

    return "\n".join(lines) + "\n"


@router.get("/approved-macs", response_class=PlainTextResponse)
async def approved_macs_list(key: str = Query(default="")):
    """Lista plana de MACs aprobadas — una por línea. Para depurar."""
    if key != SYNC_KEY:
        raise HTTPException(status_code=403, detail="Invalid key")

    now = datetime.utcnow().isoformat()
    db = await get_db()
    cursor = await db.execute(
        """SELECT d.mac_address FROM devices d
           JOIN users u ON d.user_id = u.id
           WHERE u.approval_status = 'approved' AND u.is_active = 1
             AND (u.access_expires_at IS NULL OR u.access_expires_at > ?)""",
        (now,)
    )
    rows = await cursor.fetchall()
    await db.close()
    return "\n".join(r[0] for r in rows if r[0]) + "\n"


@router.get("/approved-devices")
async def approved_devices_with_limits(key: str = Query(default="")):
    """MACs aprobadas con límites de ancho de banda para el sync_agent."""
    if key != SYNC_KEY:
        raise HTTPException(status_code=403, detail="Invalid key")

    now = datetime.utcnow().isoformat()
    db = await get_db()
    cursor = await db.execute(
        """SELECT d.mac_address, u.download_mbps, u.upload_mbps
           FROM devices d
           JOIN users u ON d.user_id = u.id
           WHERE u.approval_status = 'approved' AND u.is_active = 1
             AND (u.access_expires_at IS NULL OR u.access_expires_at > ?)""",
        (now,)
    )
    rows = await cursor.fetchall()
    await db.close()
    return [
        {"mac": r[0], "download_mbps": r[1], "upload_mbps": r[2]}
        for r in rows if r[0]
    ]


@router.get("/check-mac")
async def check_mac(mac: str = Query(default="")):
    """Verifica si una MAC está aprobada. Acceso público (sin key) para login.html."""
    if not mac:
        return {"approved": False}
    mac_upper = mac.upper().strip()
    now = datetime.utcnow().isoformat()
    db = await get_db()
    cursor = await db.execute(
        """SELECT d.id FROM devices d
           JOIN users u ON d.user_id = u.id
           WHERE UPPER(d.mac_address) = ? AND u.approval_status = 'approved' AND u.is_active = 1
             AND (u.access_expires_at IS NULL OR u.access_expires_at > ?)""",
        (mac_upper, now)
    )
    row = await cursor.fetchone()
    await db.close()
    return {"approved": bool(row), "mac": mac_upper}
