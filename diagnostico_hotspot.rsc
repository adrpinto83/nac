# ============================================================
#  Diagnóstico + Fix de hotspot NAC — pegar en WinBox Terminal
#  o ejecutar via:  ssh admin@192.168.88.1 < diagnostico_hotspot.rsc
# ============================================================

:log info "=== DIAGNOSTICO NAC HOTSPOT ==="

# ── 1. MAC del dispositivo en 192.168.100.6 ──────────────────
:local ip "192.168.100.6"
:local mac ""
:foreach h in=[/ip hotspot host find address=$ip] do={
    :set mac [/ip hotspot host get $h mac-address]
}
:if ($mac = "") do={
    :foreach h in=[/ip arp find address=$ip] do={
        :set mac [/ip arp get $h mac-address]
    }
}
:put "IP $ip → MAC: $mac"

# ── 2. Estado del hotspot service ────────────────────────────
:put "--- Hotspot services ---"
/ip hotspot print

# ── 3. Sesión activa de ese dispositivo ──────────────────────
:put "--- Sesion activa del dispositivo ---"
/ip hotspot active print where mac-address=$mac

# ── 4. Host entry del dispositivo ────────────────────────────
:put "--- Host entry ---"
/ip hotspot host print where mac-address=$mac

# ── 5. Usuario hotspot para esa MAC ──────────────────────────
:put "--- Hotspot user para esa MAC ---"
/ip hotspot user print where name=$mac

# ── 6. Reglas NAC en el forward chain ────────────────────────
:put "--- Reglas forward NAC ---"
/ip firewall filter print where chain=forward comment~"NAC:"

# ── 7. Regla established/related ─────────────────────────────
:put "--- Regla established/related ---"
/ip firewall filter print where chain=forward connection-state="established,related"

# ── 8. NAT dstnat (hotspot redirect) ─────────────────────────
:put "--- NAT dstnat (redirect hotspot) ---"
/ip firewall nat print where chain=dstnat

# ── FIX: si la MAC fue encontrada, asegurar que tenga user + regla ──
:if ($mac != "") do={
    # Agregar hotspot user si no existe
    :if ([:len [/ip hotspot user find name=$mac]] = 0) do={
        /ip hotspot user add name=$mac profile=default password="" comment=("NAC:" . $mac)
        :put "FIX: Agregado hotspot user para $mac"
        :log warning "NAC-FIX: Agregado hotspot user $mac"
    } else={
        :put "OK: hotspot user ya existe para $mac"
    }

    # Agregar forward accept antes de hs-unauth si no existe
    :if ([:len [/ip firewall filter find chain=forward src-mac-address=$mac action=accept]] = 0) do={
        :local fwdId ""
        :foreach r in=[/ip firewall filter find chain=forward action=jump jump-target=hs-unauth dynamic=yes] do={
            :set fwdId [/ip firewall filter get $r .id]
        }
        :if ($fwdId != "") do={
            /ip firewall filter add chain=forward src-mac-address=$mac action=accept \
                comment=("NAC:" . $mac) place-before=$fwdId
            :put "FIX: Agregada regla forward accept para $mac"
            :log warning "NAC-FIX: Agregada forward accept $mac"
        } else={
            /ip firewall filter add chain=forward src-mac-address=$mac action=accept \
                comment=("NAC:" . $mac)
            :put "FIX: Agregada regla forward accept (sin place-before) para $mac"
        }
    } else={
        :put "OK: regla forward ya existe para $mac"
    }

    # Asegurar regla established/related
    :if ([:len [/ip firewall filter find chain=forward comment="bypass-established"]] = 0) do={
        :local fwdId ""
        :foreach r in=[/ip firewall filter find chain=forward action=jump jump-target=hs-unauth dynamic=yes] do={
            :set fwdId [/ip firewall filter get $r .id]
        }
        :if ($fwdId != "") do={
            /ip firewall filter add chain=forward connection-state=established,related \
                action=accept comment="bypass-established" place-before=$fwdId
        } else={
            /ip firewall filter add chain=forward connection-state=established,related \
                action=accept comment="bypass-established"
        }
        :put "FIX: Agregada regla established/related"
        :log warning "NAC-FIX: Agregada bypass-established rule"
    } else={
        :put "OK: regla established/related ya existe"
    }

    # Limpiar sesión stale si la MAC está en hosts como no-autorizado
    :foreach h in=[/ip hotspot host find mac-address=$mac authorized=no] do={
        /ip hotspot host remove $h
        :put "FIX: Removida host entry stale no-autorizada para $mac"
    }

    :put "=== FIX APLICADO para $mac. Reconectar el dispositivo. ==="
} else={
    :put "ERROR: No se encontro el dispositivo en $ip"
    :put "Verifica que el dispositivo esté conectado y muestra los hosts:"
    /ip hotspot host print
    /ip arp print
}
