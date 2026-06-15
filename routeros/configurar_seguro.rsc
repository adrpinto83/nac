# MikroTik - Configuración SEGURA sin perder conectividad
# NO remueve IPs globalmente, solo lo necesario

# PASO 1: Limpiar SOLO firewall y rutas (NO addresses)
/ip firewall filter remove [find]
/ip firewall nat remove [find]
/ip firewall mangle remove [find]
/ip route remove [find]
/ip pool remove [find]
/ip dhcp-server remove [find]
/ip dhcp-server network remove [find]

# PASO 2: Mantener SOLO puerto 5 para management
# Remover addresses de otros puertos manualmente
/ip address remove [find interface!=ether5]

# PASO 3: Configurar Puerto 1 - ISP Starlink
/ip dhcp-client add interface=ether1 disabled=no comment="ISP Starlink"

# PASO 4: Configurar Puerto 3 - AP MikroTik
/ip address add address=192.168.100.1/24 interface=ether3 comment="AP"
/ip pool add name=pool-ap ranges=192.168.100.2-192.168.100.254
/ip dhcp-server add address-pool=pool-ap interface=ether3 name=dhcp-ap disabled=no
/ip dhcp-server network add address=192.168.100.0/24 gateway=192.168.100.1

# PASO 5: Servicios
/ip service enable ssh
/ip service enable rest
/ip service set rest port=80

# PASO 6: Usuario API
/user add name=api-container password=NAC_MikroTik_2025 group=write disabled=no comment="API"

# PASO 7: DNS y Identidad
/ip dns set allow-remote-requests=yes servers=8.8.8.8,8.8.4.4
/system identity set name=MikroTik-NAC-Starlink

# LISTO
