#!/usr/bin/env python3
"""
NAC Sync Agent — corre en WSL, sincroniza MACs aprobadas de Railway al router MikroTik.

Uso:
  python3 sync_agent.py            # ejecutar una vez
  python3 sync_agent.py --loop     # loop cada 60 segundos (background)
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
ROUTER_PORT  = 80           # REST API en puerto 80 (RouterOS 7.x)
ROUTER_USER  = "admin"
ROUTER_PASS  = "Mikrotik2025*"  # Contraseña del router
SYNC_COMMENT = "NAC:"       # Prefijo en comentarios de ip-binding
INTERVAL_S   = 60           # Intervalo de sync en segundos
# ──────────────────────────────────────────────────────────────────────────────


async def get_approved_macs() -> list[str]:
    """Obtiene la lista de MACs aprobadas desde Railway."""
    url = f"{RAILWAY_URL}/api/router/approved-macs?key={SYNC_KEY}"
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.get(url)
        r.raise_for_status()
        macs = [m.strip() for m in r.text.splitlines() if m.strip()]
        log.info(f"Railway → {len(macs)} MACs aprobadas")
        return macs


async def router_request(method: str, path: str, client: httpx.AsyncClient, **kwargs):
    """Wrapper para llamadas al REST API del router."""
    url = f"http://{ROUTER_HOST}:{ROUTER_PORT}/rest{path}"
    resp = await getattr(client, method)(url, **kwargs)
    resp.raise_for_status()
    # 204 No Content no tiene body
    if resp.status_code == 204 or not resp.content:
        return {}
    return resp.json()


async def sync_once(test_only: bool = False) -> bool:
    """Un ciclo de sincronización. Retorna True si tuvo éxito."""
    try:
        # 1 — Obtener MACs aprobadas de Railway
        approved = await get_approved_macs()

        # 2 — Conectar al router
        auth = (ROUTER_USER, ROUTER_PASS) if ROUTER_PASS else (ROUTER_USER, "")
        async with httpx.AsyncClient(auth=auth, verify=False, timeout=10) as router:

            # Probar conectividad
            ident = await router_request("get", "/system/identity", router)
            log.info(f"Router conectado: {ident.get('name', ROUTER_HOST)}")

            if test_only:
                log.info("Modo test — sin cambios en el router")
                return True

            # 3 — Obtener bindings actuales de NAC
            bindings = await router_request("get", "/ip/hotspot/ip-binding", router)
            if not isinstance(bindings, list):
                bindings = []

            nac_bindings = [
                b for b in bindings
                if SYNC_COMMENT in b.get("comment", "")
            ]
            current_macs = {b.get("mac-address", "").upper(): b.get(".id") for b in nac_bindings}

            # 4 — Determinar diferencias
            target_macs = {m.upper() for m in approved if m}
            to_add    = target_macs - current_macs.keys()
            to_remove = current_macs.keys() - target_macs

            # 5 — Eliminar los que ya no están aprobados
            for mac in to_remove:
                bid = current_macs[mac]
                await router_request("delete", f"/ip/hotspot/ip-binding/{bid}", router)
                log.info(f"  ✕ Removido: {mac}")

            # 6 — Agregar los nuevos
            for mac in to_add:
                await router_request("put", "/ip/hotspot/ip-binding", router, json={
                    "mac-address": mac,
                    "type": "bypassed",
                    "comment": f"{SYNC_COMMENT}nac"
                })
                log.info(f"  ✓ Agregado: {mac}")

            if not to_add and not to_remove:
                log.info("  = Sin cambios")
            else:
                log.info(f"Sync completo: +{len(to_add)} −{len(to_remove)}")

        return True

    except httpx.ConnectError as e:
        log.error(f"No se pudo conectar: {e}")
    except httpx.HTTPStatusError as e:
        log.error(f"HTTP {e.response.status_code}: {e.request.url}")
    except Exception as e:
        log.error(f"Error: {e}")

    return False


async def main():
    parser = argparse.ArgumentParser(description="NAC Sync Agent")
    parser.add_argument("--loop", action="store_true", help="Sincronizar en loop")
    parser.add_argument("--test", action="store_true", help="Solo probar conectividad")
    args = parser.parse_args()

    if args.loop:
        log.info(f"Iniciando loop de sync cada {INTERVAL_S}s — Ctrl+C para detener")
        while True:
            await sync_once(test_only=args.test)
            await asyncio.sleep(INTERVAL_S)
    else:
        ok = await sync_once(test_only=args.test)
        sys.exit(0 if ok else 1)


if __name__ == "__main__":
    asyncio.run(main())
