# ===================================================================
# MikroTik RouterOS 7.x Setup Script — NAC System Configuration
# Ejecutar en: /terminal o vía SSH
# Uso: /import file-name=router_setup.rsc
# ===================================================================

# LOG inicio
:log info "======================================================"
:log info "Iniciando limpieza y configuración del router NAC"
:log info "======================================================"

# ===================================================================
# FASE 1: LIMPIAR CONFIGURACIÓN EXISTENTE
# ===================================================================

:log info "FASE 1: Limpiando configuración antigua..."

# Limpiar reglas de firewall (filter + nat)
:log info "  - Removiendo reglas de firewall..."
/ip firewall filter remove [find]
/ip firewall nat remove [find]
/ip firewall mangle remove [find]

# Limpiar address-lists
:log info "  - Removiendo address-lists..."
/ip firewall address-list remove [find]

# Limpiar colas simples (queues)
:log info "  - Removiendo Simple Queues..."
/queue simple remove [find]

# Limpiar entradas DNS estáticas
:log info "  - Removiendo DNS estáticas..."
/ip dns static remove [find]

# Limpiar lease DHCP
:log info "  - Removiendo DHCP leases existentes..."
/ip dhcp-server lease remove [find]

# Detener y remover servidor DHCP existente
:log info "  - Removiendo DHCP server..."
/ip dhcp-server remove [find]
/ip pool remove [find]

# Deshabilitar interfaces wireless previas
:log info "  - Reseteando interfaces wireless..."
:foreach iface in=[/interface wireless find] do={
  /interface wireless set $iface disabled=yes
}

:log info "  ✓ Limpieza completada"

# ===================================================================
# FASE 2: CONFIGURACIÓN DE SERVICIOS REST API
# ===================================================================

:log info "FASE 2: Configurando REST API..."

/ip service set rest disabled=no port=80
:log info "  ✓ REST API habilitada en puerto 80"

# Verificar (comentado - puede causar error)
# :local rest_status [/ip service get [find name=rest] disabled]
# :log info "  REST API disabled=$rest_status"
:log info "  REST API configurada para puerto 80"

# ===================================================================
# FASE 3: CREAR USUARIO API
# ===================================================================

:log info "FASE 3: Creando usuario API..."

# Remover usuario anterior si existe
/user remove [find name=api-container]

# Crear usuario api-container
/user add name=api-container password=NAC_MikroTik_2025 group=read
:log info "  ✓ Usuario 'api-container' creado"

# ===================================================================
# FASE 4: CONFIGURAR LISTAS DE CONTROL DE ACCESO (ADDRESS-LISTS)
# ===================================================================

:log info "FASE 4: Creando listas de control (whitelist/blocklist)..."

# Crear lista whitelist (vacía inicialmente - será poblada por la app)
/ip firewall address-list add list=mac-whitelist address=00:00:00:00:00:00 \
  comment="Placeholder - gestionar desde NAC app" disabled=yes

# Crear lista blocklist (vacía inicialmente)
/ip firewall address-list add list=mac-blocked address=00:00:00:00:00:00 \
  comment="Placeholder - gestionar desde NAC app" disabled=yes

:log info "  ✓ Address-lists creadas (mac-whitelist, mac-blocked)"

# ===================================================================
# FASE 5: CONFIGURAR REGLAS DE FIREWALL (FAILSAFE)
# ===================================================================

:log info "FASE 5: Configurando reglas de firewall failsafe..."

# Identificar interfaz LAN (asumiendo bridge-lan o ether2)
:local lan_iface "bridge-lan"
:if ([/interface find name=$lan_iface] = "") do={
  :set lan_iface "ether2"
}
:if ([/interface find name=$lan_iface] = "") do={
  :set lan_iface "ether3"
}

:log info ("  LAN interface detectada: " . $lan_iface)

# Regla 0: ACCEPT si MAC está en whitelist
/ip firewall filter add chain=forward \
  src-address-list=mac-whitelist \
  action=accept \
  comment="ACCEPT whitelisted MACs" \
  disabled=no \
  place-before=0

:log info "  ✓ Regla 0: ACCEPT whitelisted"

# Regla 1: DROP si MAC está en blocklist
/ip firewall filter add chain=forward \
  src-address-list=mac-blocked \
  action=drop \
  comment="DROP blocked MACs" \
  disabled=no

:log info "  ✓ Regla 1: DROP blocked"

# Regla 2: DROP default-deny (deshabilitada inicialmente, activar si es necesario)
/ip firewall filter add chain=forward \
  in-interface=$lan_iface \
  action=drop \
  comment="DROP unknown MACs (default-deny policy - DESHABILITADO)" \
  disabled=yes

:log info "  ✓ Regla 2: DROP unknown (disabled)"

# NAT rule: MASQUERADE (si WAN es ether1)
/ip firewall nat add chain=srcnat out-interface=ether1 \
  action=masquerade \
  comment="LAN to WAN NAT"

:log info "  ✓ NAT rule configurada"

# ===================================================================
# FASE 6: CONFIGURAR INTERFAZ WIRELESS
# ===================================================================

:log info "FASE 6: Configurando wireless..."

# Obtener nombre de interfaz wireless principal (wlan1 o wlan2)
:local wifi_iface [/interface wireless find wireless-protocol~"802.11ac"]
:if ([:len $wifi_iface] = 0) do={
  :set wifi_iface [/interface wireless find]
}
:local wifi_name [/interface wireless get $wifi_iface name]

:log info ("  Interfaz wireless encontrada: " . $wifi_name)

# Crear perfil de seguridad "open-ds1405" (sin autenticación)
:local sec_profile_exists [/interface wireless security-profiles find name=open-ds1405]
:if ([:len $sec_profile_exists] = 0) do={
  /interface wireless security-profiles add \
    name=open-ds1405 \
    mode=open \
    authentication-types="" \
    unicast-ciphers=ccmp \
    group-ciphers=ccmp
  :log info "  ✓ Perfil de seguridad 'open-ds1405' creado"
} else {
  :log info "  ! Perfil de seguridad 'open-ds1405' ya existe"
}

# Configurar interfaz wireless
/interface wireless set $wifi_name \
  disabled=no \
  mode=ap-bridge \
  band=5GHz-A \
  channel-width=80MHz \
  frequency=auto \
  ssid="DS-1405-PDVSA" \
  hide-ssid=yes \
  security-profile=open-ds1405 \
  tx-power=20

:log info "  ✓ SSID configurado: 'DS-1405-PDVSA' (oculto, open, 5GHz)"

# ===================================================================
# FASE 7: CONFIGURAR DHCP SERVER
# ===================================================================

:log info "FASE 7: Configurando DHCP..."

# Crear pool DHCP (192.168.88.100 - 192.168.88.200)
/ip pool add name=dhcp-pool ranges=192.168.88.100-192.168.88.200
:log info "  ✓ Pool DHCP creado (192.168.88.100-200)"

# Crear servidor DHCP en bridge-lan
/ip dhcp-server add interface=$lan_iface address-pool=dhcp-pool \
  name=dhcp-server disabled=no
:log info "  ✓ DHCP server habilitado en $lan_iface"

# Configurar red DHCP
/ip dhcp-server network add address=192.168.88.0/24 \
  gateway=192.168.88.1 \
  dns-server=8.8.8.8,8.8.4.4 \
  ntp-server=pool.ntp.org \
  comment="LAN DHCP - NAC System"
:log info "  ✓ DHCP network configurada"

# ===================================================================
# FASE 8: CONFIGURAR DNS
# ===================================================================

:log info "FASE 8: Configurando DNS..."

# Habilitar DNS server
/ip dns set allow-remote-requests=yes cache-size=8192 cache-max-ttl=1d
:log info "  ✓ DNS server habilitado"

# ===================================================================
# FASE 9: VERIFICACIÓN FINAL
# ===================================================================

:log info "FASE 9: Verificación final..."

:local firewall_count [/ip firewall filter print count-only where chain=forward]
:local whitelist_count [/ip firewall address-list print count-only where list=mac-whitelist]
:local blocklist_count [/ip firewall address-list where list=mac-blocked print count-only]
:local queue_count [/queue simple print count-only]
:local dns_static_count [/ip dns static print count-only]

:log info "======================================================"
:log info "CONFIGURACIÓN COMPLETADA"
:log info "======================================================"
:log info ("Firewall rules (forward): " . $firewall_count)
:log info ("MAC whitelist entries: " . $whitelist_count)
:log info ("MAC blocklist entries: " . $blocklist_count)
:log info ("Simple Queues: " . $queue_count)
:log info ("DNS static entries: " . $dns_static_count)
:log info "======================================================"

:log info "PASOS SIGUIENTES:"
:log info "1. Verificar desde PC: curl -u api-container:NAC_MikroTik_2025 http://192.168.88.1:80/rest/system/identity"
:log info "2. Conectar la PC al router (WiFi 'DS-1405-PDVSA' o cable)"
:log info "3. Ejecutar la aplicación NAC en la PC"
:log info "======================================================"
