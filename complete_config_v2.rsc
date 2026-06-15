# ===================================================================
# Script para completar la configuración NAC (versión 2)
# ===================================================================

:log info "====== Completando configuración NAC ======"

# ===== CREAR/LIMPIAR ADDRESS-LISTS =====
:log info "Configurando address-lists..."
/ip firewall address-list remove [find list=mac-whitelist]
/ip firewall address-list remove [find list=mac-blocked]
/ip firewall address-list add list=mac-whitelist address=00:00:00:00:00:00 comment="Whitelist placeholder" disabled=yes
/ip firewall address-list add list=mac-blocked address=00:00:00:00:00:00 comment="Blocklist placeholder" disabled=yes
:log info "✓ Address-lists configuradas"

# ===== HABILITAR DHCP =====
:log info "Habilitando DHCP server..."
/ip dhcp-server set [find name=dhcp-server] disabled=no
:log info "✓ DHCP habilitado"

# ===== CONFIGURAR INTERFAZ WIRELESS =====
:log info "Configurando SSID..."
/interface wireless set [find] disabled=no ssid=DS-1405-PDVSA hide-ssid=yes
:log info "✓ SSID configurado"

# ===== CREAR PERFILES DE QoS =====
:log info "Creando perfiles de QoS..."
/queue simple remove [find name~"NAC-"]
/queue simple add name=NAC-ADMIN target=10.0.0.1/32 max-limit=unlimited disabled=yes comment="Admin"
/queue simple add name=NAC-PROFESIONAL target=10.0.0.2/32 max-limit=10M/5M disabled=yes comment="Profesional"
/queue simple add name=NAC-ESTANDAR target=10.0.0.3/32 max-limit=5M/2M disabled=yes comment="Estandar"
/queue simple add name=NAC-INVITADO target=10.0.0.4/32 max-limit=2M/1M disabled=yes comment="Invitado"
:log info "✓ Perfiles QoS creados"

:log info "====== ✓ COMPLETADO ======"
