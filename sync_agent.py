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


async def get_approved_devices() -> list[dict]:
    """Retorna lista de {mac, download_mbps, upload_mbps} desde Railway."""
    url = f"{RAILWAY_URL}/api/router/approved-devices?key={SYNC_KEY}"
    text = None
    # httpx a veces falla con SSL handshake timeout en WSL; curl es confiable.
    try:
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.get(url)
            r.raise_for_status()
            text = r.text
    except Exception as e:
        log.warning(f"httpx falló ({type(e).__name__}), usando curl…")
        proc = await asyncio.create_subprocess_exec(
            "curl", "-4", "-sf", "--max-time", "20", url,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        out, err = await proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(f"curl falló: {err.decode()[:200]}")
        text = out.decode()

    import json as _json
    devices = _json.loads(text)
    log.info(f"Railway → {len(devices)} dispositivos aprobados")
    return devices


def build_rate_limit(dl: int | None, ul: int | None) -> str:
    """Convierte Mbps a formato MikroTik rate-limit 'DLM/ULM'. Vacío = sin límite."""
    if not dl and not ul:
        return ""
    d = f"{dl}M" if dl else "0"
    u = f"{ul}M" if ul else "0"
    return f"{d}/{u}"


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
        devices = await get_approved_devices()
        auth = (ROUTER_USER, ROUTER_PASS)

        async with httpx.AsyncClient(auth=auth, verify=False, timeout=10) as r:
            ident = await router_request("get", "/system/identity", r)
            log.info(f"Router: {ident.get('name', ROUTER_HOST)}")

            if test_only:
                log.info("Modo test — sin cambios")
                return True

            # target: {MAC_UPPER: {download_mbps, upload_mbps}}
            target: dict[str, dict] = {
                d["mac"].upper(): d for d in devices if d.get("mac")
            }

            # Descubrir ID del forward hs-unauth jump
            fwd_unauth_id, flt_rules = await get_fwd_unauth_id(r)

            # ── Hotspot users (MAC auto-login) ─────────────────────────────────
            # IMPORTANTE: el perfil usa mac-auth-mode=mac-as-username, así que el
            # NOMBRE del usuario debe ser exactamente la MAC (mayúsculas, con ":").
            # Si no, el login-by=mac nunca encuentra al usuario y falla.
            users = await router_request("get", "/ip/hotspot/user", r)
            if not isinstance(users, list):
                users = []
            # nac_u: {MAC_UPPER: {".id": ..., "rate-limit": ...}}
            nac_u = {u.get("name", "").upper(): u
                     for u in users if COMMENT in u.get("comment", "")}

            for mac in target.keys() - nac_u.keys():
                dl = target[mac].get("download_mbps")
                ul = target[mac].get("upload_mbps")
                rate = build_rate_limit(dl, ul)
                body = {
                    "name": mac,
                    "profile": "default",
                    "password": "",
                    "comment": nac_comment(mac),
                }
                if rate:
                    body["rate-limit"] = rate
                await router_request("put", "/ip/hotspot/user", r, json=body)
                log.info(f"  +hs-user: {mac}" + (f" rate={rate}" if rate else ""))

            # Actualizar rate-limit si cambió para usuarios ya existentes
            for name, udata in nac_u.items():
                if name not in target:
                    continue
                uid = udata.get(".id")
                dl = target[name].get("download_mbps")
                ul = target[name].get("upload_mbps")
                new_rate = build_rate_limit(dl, ul)
                cur_rate = udata.get("rate-limit", "")
                if new_rate != cur_rate:
                    patch = {"rate-limit": new_rate} if new_rate else {"rate-limit": ""}
                    await router_request("patch", f"/ip/hotspot/user/{uid}", r, json=patch)
                    log.info(f"  ~hs-user rate: {name} {cur_rate!r} → {new_rate!r}")

            for name, udata in nac_u.items():
                uid = udata.get(".id")
                if name not in target:
                    await router_request("delete", f"/ip/hotspot/user/{uid}", r)
                    log.info(f"  -hs-user: {name}")
                    # Limpiar sesión activa y host stale para que el
                    # dispositivo no quede con auth=true residual
                    try:
                        active = await router_request("get", "/ip/hotspot/active", r)
                        for a in (active if isinstance(active, list) else []):
                            if a.get("mac-address", "").upper() == name.upper():
                                await router_request("delete", f"/ip/hotspot/active/{a.get('.id')}", r)
                                log.info(f"  -hs-active: {name}")
                        hosts = await router_request("get", "/ip/hotspot/host", r)
                        for h in (hosts if isinstance(hosts, list) else []):
                            if h.get("mac-address", "").upper() == name.upper():
                                await router_request("delete", f"/ip/hotspot/host/{h.get('.id')}", r)
                                log.info(f"  -hs-host: {name}")
                    except Exception as e:
                        log.warning(f"  limpieza sesión {name}: {e}")

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

            for mac in target.keys() - nac_flt.keys():
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
