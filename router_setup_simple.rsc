# ===================================================================
# MikroTik RouterOS 7.x Setup Script — Versión Simplificada
# Ejecutar en: /terminal o vía SSH
# ===================================================================

:log info "====== Iniciando configuración NAC ======"

# ===== LIMPIAR CONFIGURACIÓN ANTIGUA =====
:log info "Limpiando configuración anterior..."
/ip firewall filter remove [find]
/ip firewall nat remove [find]
/ip firewall mangle remove [find]
/ip firewall address-list remove [find]
/queue simple remove [find]
/ip dns static remove [find]
/ip dhcp-server lease remove [find]
/ip dhcp-server remove [find]
/ip pool remove [find]
:log info "✓ Limpieza completada"

# ===== HABILITAR REST API =====
:log info "Habilitando REST API en puerto 80..."
/ip service set rest disabled=no port=80
:log info "✓ REST API habilitada"

# ===== CREAR USUARIO API =====
:log info "Creando usuario API..."
/user remove [find name=api-container]
/user add name=api-container password=NAC_MikroTik_2025 group=read
:log info "✓ Usuario api-container creado"

# ===== CREAR LISTAS DE CONTROL =====
:log info "Creando listas de control..."
/ip firewall address-list add list=mac-whitelist address=00:00:00:00:00:00 comment="Placeholder" disabled=yes
/ip firewall address-list add list=mac-blocked address=00:00:00:00:00:00 comment="Placeholder" disabled=yes
:log info "✓ Address-lists creadas"

# ===== CONFIGURAR FIREWALL =====
:log info "Configurando firewall rules..."
/ip firewall filter add chain=forward src-address-list=mac-whitelist action=accept comment="ACCEPT whitelisted" disabled=no place-before=0
/ip firewall filter add chain=forward src-address-list=mac-blocked action=drop comment="DROP blocked" disabled=no
/ip firewall nat add chain=srcnat out-interface=ether1 action=masquerade comment="LAN to WAN NAT"
:log info "✓ Firewall configurado"

# ===== CONFIGURAR WIRELESS =====
:log info "Configurando wireless..."
/interface wireless security-profiles add name=open-ds1405 mode=open authentication-types="" unicast-ciphers=ccmp group-ciphers=ccmp
/interface wireless set [find] disabled=no mode=ap-bridge band=5GHz-A channel-width=80MHz frequency=auto ssid=DS-1405-PDVSA hide-ssid=yes security-profile=open-ds1405 tx-power=20
:log info "✓ SSID configurado: DS-1405-PDVSA"

# ===== CONFIGURAR DHCP =====
:log info "Configurando DHCP..."
/ip pool add name=dhcp-pool ranges=192.168.88.100-192.168.88.200
/ip dhcp-server add interface=bridge-lan address-pool=dhcp-pool name=dhcp-server disabled=no
/ip dhcp-server network add address=192.168.88.0/24 gateway=192.168.88.1 dns-server=8.8.8.8,8.8.4.4 ntp-server=pool.ntp.org comment="LAN DHCP"
:log info "✓ DHCP configurado"

# ===== CONFIGURAR DNS =====
:log info "Configurando DNS..."
/ip dns set allow-remote-requests=yes cache-size=8192 cache-max-ttl=1d
:log info "✓ DNS habilitado"

# ===== FINALIZAR =====
:log info "====== ✓ CONFIGURACIÓN COMPLETADA ======"
:log info "Usuario API: api-container / NAC_MikroTik_2025"
:log info "REST API: http://192.168.88.1:80/rest"
:log info "SSID: DS-1405-PDVSA (oculto)"
