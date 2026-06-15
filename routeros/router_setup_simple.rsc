# MikroTik hAP ac3 - Configuración Simple para NAC System
# Solo configuración básica - la aplicación NAC va en la PC

# ============================================================================
# LIMPIEZA
# ============================================================================

/interface bridge remove [find]
/ip address remove [find]
/ip firewall nat remove [find]
/ip firewall filter remove [find]
/ip route remove [find]
/ip pool remove [find]
/ip dhcp-server remove [find]
/ip dhcp-server network remove [find]

# ============================================================================
# CONFIGURAR IP LOCAL DEL ROUTER
# ============================================================================

# Puerto 4 es donde está conectado el usuario (local)
/ip address add address=192.168.88.1/24 interface=ether4 comment="Local Management"

# ============================================================================
# DHCP SERVER PARA RED LOCAL
# ============================================================================

/ip pool add name=dhcp-local ranges=192.168.88.10-192.168.88.254

/ip dhcp-server add address-pool=dhcp-local interface=ether4 \
    name=dhcp-local disabled=no

/ip dhcp-server network add address=192.168.88.0/24 gateway=192.168.88.1 \
    comment="Local Network"

# ============================================================================
# FIREWALL - PERMITIR TODO LOCALMENTE
# ============================================================================

# Aceptar conexiones establecidas
/ip firewall filter add action=accept chain=input connection-state=established,related \
    comment="Allow established"

# Aceptar desde redes locales
/ip firewall filter add action=accept chain=input src-address=192.168.0.0/16 \
    comment="Allow local"

# Aceptar ICMP (ping)
/ip firewall filter add action=accept chain=input protocol=icmp \
    comment="Allow ICMP"

# Aceptar forward establecido
/ip firewall filter add action=accept chain=forward connection-state=established,related \
    comment="Allow forward established"

# Aceptar forward desde local
/ip firewall filter add action=accept chain=forward src-address=192.168.88.0/24 \
    comment="Allow forward from local"

# NAT para salida
/ip firewall nat add action=masquerade chain=srcnat out-interface=ether1 \
    comment="NAT for WAN"

# ============================================================================
# HABILITAR REST API (para NAC System)
# ============================================================================

/ip service enable rest
/ip service set rest port=80

# ============================================================================
# CREAR USUARIO API
# ============================================================================

/user add name=api-container password=NAC_MikroTik_2025 group=write disabled=no \
    comment="API user for NAC"

# ============================================================================
# CONFIGURACIÓN BASICA
# ============================================================================

/system identity set name=MikroTik-NAC-Router

/ip dns set allow-remote-requests=yes servers=8.8.8.8,8.8.4.4

/system ntp client set enabled=yes servers=0.pool.ntp.org

# ============================================================================
# PUERTO 1 - ISP (DHCP)
# ============================================================================

/ip dhcp-client add interface=ether1 disabled=no comment="ISP Connection"

# ============================================================================
# FINAL
# ============================================================================

# Ahora el router tiene:
# - IP local: 192.168.88.1 (puerto 4 donde está tu PC)
# - REST API: http://192.168.88.1
# - Usuario: admin / (sin contraseña por defecto)
# - Usuario API: api-container / NAC_MikroTik_2025
# - DHCP: 192.168.88.10-254
# - ISP: Puerto 1 (DHCP)

# Para Dual ISP, AP, etc., configúralo desde la aplicación NAC en tu PC
