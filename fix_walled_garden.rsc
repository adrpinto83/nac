# ============================================================
#  Walled Garden — Railway Portal Cautivo
#  Permite acceso al splash page sin autenticación
#  Pegar en WinBox → New Terminal  o  ssh admin@192.168.88.1
# ============================================================

:local PORTAL_HOST "nac-production.up.railway.app"

# ── Walled garden por hostname (HTTP GET) ─────────────────────────────────────
:if ([:len [/ip hotspot walled-garden find dst-host=$PORTAL_HOST]] = 0) do={
    /ip hotspot walled-garden add \
        dst-host=$PORTAL_HOST \
        comment="NAC-portal"
    :put "OK: walled-garden hostname agregado ($PORTAL_HOST)"
} else={
    :put "INFO: walled-garden hostname ya existia ($PORTAL_HOST)"
}

# ── Walled garden IP (fallback HTTPS / CDN) ───────────────────────────────────
:if ([:len [/ip hotspot walled-garden ip find comment="NAC-portal-ip"]] = 0) do={
    /ip hotspot walled-garden ip add \
        dst-host=$PORTAL_HOST \
        action=accept \
        comment="NAC-portal-ip"
    :put "OK: walled-garden ip agregado ($PORTAL_HOST)"
} else={
    :put "INFO: walled-garden ip ya existia"
}

# ── Verificar resultado ───────────────────────────────────────────────────────
:put "--- Walled garden actual ---"
/ip hotspot walled-garden print
/ip hotspot walled-garden ip print

:put "============================================"
:put "LISTO: el portal splash es accesible sin login."
:put "Pide al usuario que recargue la pagina."
:put "============================================"
