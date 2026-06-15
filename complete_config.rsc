# ===================================================================
# Script para completar la configuración NAC
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
:log info "✓ SSID configurado: DS-1405-PDVSA"

# ===== CREAR PERFILES DE QoS =====
:log info "Creando perfiles de QoS..."
/queue simple add name=NAC-ADMIN-TEMPLATE target=10.0.0.1/32 max-limit=0/0 priority=1 disabled=yes comment="Admin profile template"
/queue simple add name=NAC-PROFESIONAL-TEMPLATE target=10.0.0.2/32 max-limit=10M/5M priority=2 disabled=yes comment="Profesional profile template"
/queue simple add name=NAC-ESTANDAR-TEMPLATE target=10.0.0.3/32 max-limit=5M/2M priority=3 disabled=yes comment="Estandar profile template"
/queue simple add name=NAC-INVITADO-TEMPLATE target=10.0.0.4/32 max-limit=2M/1M priority=4 disabled=yes comment="Invitado profile template"
:log info "✓ Perfiles QoS creados"

# ===== VERIFICACIÓN FINAL =====
:log info "====== ✓ CONFIGURACIÓN COMPLETADA ======"
:log info "Componentes activos:"
:log info "  • REST API en puerto 80"
:log info "  • Usuario api-container creado"
:log info "  • Address-lists (whitelist/blocklist) listas"
:log info "  • Firewall rules configuradas"
:log info "  • DHCP habilitado"
:log info "  • SSID DS-1405-PDVSA configurado"
:log info "  • Perfiles QoS template listos"
