#!/usr/bin/env python3
"""
NAC Sync Agent — corre en WSL, sincroniza MACs aprobadas de Railway al router MikroTik.

Aplica 3 elementos por MAC aprobado:
  1. hotspot user con mac-address (login.html hace auto-login via $(username))
  2. forward filter accept before hs-unauth (tráfico saliente mientras auth=true)
  3. forward established/related accept (tráfico de retorno desde internet)

NO usa ip-binding bypassed ni dstnat RETURN porque eso impide que el hotspot
intercepte el primer HTTP y autentique al dispositivo (auth=true via login.html).

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
COMMENT      = "NAC:"
INTERVAL_S   = 60
# ──────────────────────────────────────────────────────────────────────────────


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


async def get_fwd_unauth_id(r: httpx.AsyncClient) -> str:
    """Descubre el ID actual del forward hs-unauth jump (cambia con cada reinicio)."""
    flt_rules = await router_request("get", "/ip/firewall/filter", r)
    for rule in (flt_rules if isinstance(flt_rules, list) else []):
        if (rule.get("chain") == "forward"
                and rule.get("action") == "jump"
                and rule.get("jump-target") == "hs-unauth"
                and rule.get("dynamic") == "true"):
            fwd_id = rule.get(".id")
            log.info(f"  fwd-unauth jump ID: {fwd_id}")
            return fwd_id, flt_rules
    log.warning("  No se encontró fwd-unauth jump, usando *7D como fallback")
    return "*7D", flt_rules


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

            target = {m.upper() for m in approved if m}

            # Descubrir ID del forward hs-unauth jump
            fwd_unauth_id, flt_rules = await get_fwd_unauth_id(r)

            # ── Hotspot users (MAC auto-login via login.html) ──────────────────
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

            # ── Forward filter accept por MAC (before hs-unauth jump) ──────────
            if not isinstance(flt_rules, list):
                flt_rules = []
            nac_flt = {
                rule.get("src-mac-address", "").upper(): rule.get(".id")
                for rule in flt_rules
                if rule.get("chain") == "forward"
                and COMMENT in rule.get("comment", "")
                and rule.get("action") == "accept"
                and rule.get("src-mac-address", "")
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

            # ── Forward established/related (tráfico de retorno desde internet) ─
            ESTAB_COMMENT = "bypass-established"
            has_estab = any(
                rule.get("chain") == "forward"
                and rule.get("connection-state", "").startswith("established")
                and rule.get("action") == "accept"
                and rule.get("comment", "") == ESTAB_COMMENT
                for rule in flt_rules
            )
            if not has_estab:
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

            # ── Limpiar ip-binding y dstnat RETURN que hayan quedado de versiones anteriores ──
            bindings = await router_request("get", "/ip/hotspot/ip-binding", r)
            for b in (bindings if isinstance(bindings, list) else []):
                if COMMENT in b.get("comment", ""):
                    await router_request("delete", f"/ip/hotspot/ip-binding/{b.get('.id')}", r)
                    log.info(f"  -binding (legacy): {b.get('mac-address')}")

            nat_rules = await router_request("get", "/ip/firewall/nat", r)
            for rule in (nat_rules if isinstance(nat_rules, list) else []):
                if (rule.get("chain") == "dstnat"
                        and COMMENT in rule.get("comment", "")
                        and rule.get("action") == "return"):
                    await router_request("delete", f"/ip/firewall/nat/{rule.get('.id')}", r)
                    log.info(f"  -nat-return (legacy): {rule.get('src-mac-address')}")

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
