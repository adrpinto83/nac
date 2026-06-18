#!/usr/bin/env python3
"""
NAC Sync Agent — corre en WSL, sincroniza MACs aprobadas de Railway al router MikroTik.

Aplica 4 reglas por MAC aprobado:
  1. ip-binding type=bypassed  (hotspot tracking bypass)
  2. hotspot user con mac-address (auto-login por MAC)
  3. NAT dstnat return          (no redirigir al proxy)
  4. forward filter accept      (pasar la cadena hs-unauth)

Uso:
  python3 sync_agent.py            # ejecutar una vez
  python3 sync_agent.py --loop     # loop cada 60 segundos
  python3 sync_agent.py --test     # probar conectividad sin cambios
"""

import sys
import time
import httpx
import asyncio
import logging
import argparse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("nac-sync")

# ── Configuración ──────────────────────────────────────────────────────────────
RAILWAY_URL  = "https://nac-production.up.railway.app"
SYNC_KEY     = "nac-sync-2024"
ROUTER_HOST  = "192.168.88.1"
ROUTER_PORT  = 80
ROUTER_USER  = "admin"
ROUTER_PASS  = "Mikrotik2025*"
COMMENT      = "NAC:"       # Prefijo para identificar todas las reglas NAC
INTERVAL_S   = 60
# ──────────────────────────────────────────────────────────────────────────────

HOTSPOT_JUMP_ID = "*70"   # Actualizado dinámicamente en sync_once()
FWD_UNAUTH_ID   = "*7D"   # Actualizado dinámicamente en sync_once()


async def get_dynamic_ids(r: httpx.AsyncClient) -> tuple[str, str]:
    """Descubre los IDs actuales del hotspot jump (dstnat) y hs-unauth jump (forward)."""
    hs_id = HOTSPOT_JUMP_ID
    fwd_id = FWD_UNAUTH_ID

    nat_rules = await router_request("get", "/ip/firewall/nat", r)
    for rule in (nat_rules if isinstance(nat_rules, list) else []):
        if (rule.get("chain") == "dstnat"
                and rule.get("action") == "jump"
                and rule.get("dynamic") == "true"):
            hs_id = rule.get(".id", hs_id)
            break

    flt_rules = await router_request("get", "/ip/firewall/filter", r)
    for rule in (flt_rules if isinstance(flt_rules, list) else []):
        if (rule.get("chain") == "forward"
                and rule.get("action") == "jump"
                and rule.get("jump-target") == "hs-unauth"
                and rule.get("dynamic") == "true"):
            fwd_id = rule.get(".id", fwd_id)
            break

    log.info(f"  IDs dinámicos: hotspot-jump={hs_id}  fwd-unauth={fwd_id}")
    return hs_id, fwd_id


async def get_approved_macs() -> list[str]:
    url = f"{RAILWAY_URL}/api/router/approved-macs?key={SYNC_KEY}"
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.get(url)
        r.raise_for_status()
        macs = [m.strip().upper() for m in r.text.splitlines() if m.strip()]
        log.info(f"Railway → {len(macs)} MACs aprobadas")
        return macs


async def router_request(method: str, path: str, client: httpx.AsyncClient, **kwargs):
    url = f"http://{ROUTER_HOST}:{ROUTER_PORT}/rest{path}"
    resp = await getattr(client, method)(url, **kwargs)
    resp.raise_for_status()
    if resp.status_code == 204 or not resp.content:
        return {}
    return resp.json()


def nac_comment(mac: str) -> str:
    return f"{COMMENT}{mac}"


async def sync_once(test_only: bool = False) -> bool:
    try:
        approved = await get_approved_macs()
        auth = (ROUTER_USER, ROUTER_PASS)

        async with httpx.AsyncClient(auth=auth, verify=False, timeout=10) as r:
            ident = await router_request("get", "/system/identity", r)
            log.info(f"Router: {ident.get('name', ROUTER_HOST)}")

            if test_only:
                log.info("Modo test — sin cambios")
                return True

            # Descubrir IDs dinámicos del hotspot
            hotspot_jump_id, fwd_unauth_id = await get_dynamic_ids(r)

            target = {m.upper() for m in approved if m}

            # ── ip-binding ────────────────────────────────────────────────────
            bindings = await router_request("get", "/ip/hotspot/ip-binding", r)
            if not isinstance(bindings, list):
                bindings = []
            nac_b = {b.get("mac-address", "").upper(): b.get(".id")
                     for b in bindings if COMMENT in b.get("comment", "")}

            for mac in target - nac_b.keys():
                await router_request("put", "/ip/hotspot/ip-binding", r, json={
                    "mac-address": mac,
                    "type": "bypassed",
                    "comment": nac_comment(mac)
                })
                log.info(f"  +binding: {mac}")
            for mac, bid in nac_b.items():
                if mac not in target:
                    await router_request("delete", f"/ip/hotspot/ip-binding/{bid}", r)
                    log.info(f"  -binding: {mac}")

            # ── hotspot users (MAC auto-login) ────────────────────────────────
            users = await router_request("get", "/ip/hotspot/user", r)
            if not isinstance(users, list):
                users = []
            nac_u = {u.get("mac-address", "").upper(): u.get(".id")
                     for u in users if COMMENT in u.get("comment", "")}

            for mac in target - nac_u.keys():
                username = mac.lower().replace(":", "")
                await router_request("put", "/ip/hotspot/user", r, json={
                    "name": username,
                    "mac-address": mac,
                    "profile": "default",
                    "password": "",
                    "comment": nac_comment(mac)
                })
                log.info(f"  +hs-user: {mac}")
            for mac, uid in nac_u.items():
                if mac not in target:
                    await router_request("delete", f"/ip/hotspot/user/{uid}", r)
                    log.info(f"  -hs-user: {mac}")

            # ── NAT dstnat return (bypass proxy redirect) ─────────────────────
            nat_rules = await router_request("get", "/ip/firewall/nat", r)
            if not isinstance(nat_rules, list):
                nat_rules = []
            nac_nat = {
                rule.get("src-mac-address", "").upper(): rule.get(".id")
                for rule in nat_rules
                if rule.get("chain") == "dstnat"
                and COMMENT in rule.get("comment", "")
                and rule.get("action") == "return"
            }

            for mac in target - nac_nat.keys():
                await router_request("put", "/ip/firewall/nat", r, json={
                    "chain": "dstnat",
                    "src-mac-address": mac,
                    "action": "return",
                    "comment": nac_comment(mac),
                    "place-before": hotspot_jump_id
                })
                log.info(f"  +nat-bypass: {mac}")
            for mac, nid in nac_nat.items():
                if mac not in target:
                    await router_request("delete", f"/ip/firewall/nat/{nid}", r)
                    log.info(f"  -nat-bypass: {mac}")

            # ── Forward filter accept por MAC (before hs-unauth jump) ────────
            flt_rules = await router_request("get", "/ip/firewall/filter", r)
            if not isinstance(flt_rules, list):
                flt_rules = []
            nac_flt = {
                rule.get("src-mac-address", "").upper(): rule.get(".id")
                for rule in flt_rules
                if rule.get("chain") == "forward"
                and COMMENT in rule.get("comment", "")
                and rule.get("action") == "accept"
                and rule.get("src-mac-address", "")  # solo reglas con MAC
            }

            for mac in target - nac_flt.keys():
                await router_request("put", "/ip/firewall/filter", r, json={
                    "chain": "forward",
                    "src-mac-address": mac,
                    "action": "accept",
                    "comment": nac_comment(mac),
                    "place-before": fwd_unauth_id
                })
                log.info(f"  +fwd-accept: {mac}")
            for mac, fid in nac_flt.items():
                if mac not in target:
                    await router_request("delete", f"/ip/firewall/filter/{fid}", r)
                    log.info(f"  -fwd-accept: {mac}")

            # ── Forward established/related (tráfico de retorno desde internet)
            # Acepta respuestas inbound ANTES de hs-unauth, que solo bloquea NEW.
            # Comentario sin "NAC:" para que este bloque no la gestione ni borre.
            ESTAB_COMMENT = "bypass-established"
            has_estab = any(
                rule.get("chain") == "forward"
                and rule.get("connection-state", "").startswith("established")
                and rule.get("action") == "accept"
                and rule.get("comment", "") == ESTAB_COMMENT
                for rule in flt_rules
            )
            if not has_estab:
                # Verificar en la lista actualizada (puede que la tenga otro sync)
                flt_rules2 = await router_request("get", "/ip/firewall/filter", r)
                has_estab = any(
                    rule.get("chain") == "forward"
                    and rule.get("connection-state", "").startswith("established")
                    and rule.get("action") == "accept"
                    and rule.get("comment", "") == ESTAB_COMMENT
                    for rule in (flt_rules2 if isinstance(flt_rules2, list) else [])
                )
                if not has_estab:
                    await router_request("put", "/ip/firewall/filter", r, json={
                        "chain": "forward",
                        "connection-state": "established,related",
                        "action": "accept",
                        "comment": ESTAB_COMMENT,
                        "place-before": fwd_unauth_id
                    })
                    log.info("  +fwd-established: bypass-established rule added")

            log.info("Sync completo")
        return True

    except httpx.ConnectError as e:
        log.error(f"No se pudo conectar: {e}")
    except httpx.HTTPStatusError as e:
        log.error(f"HTTP {e.response.status_code}: {e.request.url}")
    except Exception as e:
        log.exception(f"Error: {e}")
    return False


async def main():
    parser = argparse.ArgumentParser(description="NAC Sync Agent")
    parser.add_argument("--loop", action="store_true")
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()

    if args.loop:
        log.info(f"Loop cada {INTERVAL_S}s — Ctrl+C para detener")
        while True:
            await sync_once(test_only=args.test)
            await asyncio.sleep(INTERVAL_S)
    else:
        ok = await sync_once(test_only=args.test)
        sys.exit(0 if ok else 1)


if __name__ == "__main__":
    asyncio.run(main())
