# MikroTik hAP ac3 - Configuración Dual ISP + APs + Balanceo de Carga
# Puerto 1: ISP 1
# Puerto 2: ISP 2
# Puertos 3-5: Access Points
# Puertos 6-10: LAN local + gerencia

# ============================================================================
# FASE 1: Limpieza Completa
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
# FASE 2: Configuración de Interfaces Físicas
# ============================================================================

# Renombrar interfaces para claridad
/interface set numbers=0 name=ether1-isp1
/interface set numbers=1 name=ether2-isp2
/interface set numbers=2 name=ether3-ap
/interface set numbers=3 name=ether4-ap
/interface set numbers=4 name=ether5-ap
/interface set numbers=5 name=ether6-lan
/interface set numbers=6 name=ether7-gerencia

# ============================================================================
# FASE 3: Configuración de Bridges para VLAN
# ============================================================================

# Bridge para ISP 1
/interface bridge add name=bridge-isp1 comment="Bridge ISP 1"
/interface bridge port add bridge=bridge-isp1 interface=ether1-isp1

# Bridge para ISP 2
/interface bridge add name=bridge-isp2 comment="Bridge ISP 2"
/interface bridge port add bridge=bridge-isp2 interface=ether2-isp2

# Bridge para Access Points (VLAN 100)
/interface bridge add name=bridge-aps comment="Bridge para APs"
/interface bridge port add bridge=bridge-aps interface=ether3-ap
/interface bridge port add bridge=bridge-aps interface=ether4-ap
/interface bridge port add bridge=bridge-aps interface=ether5-ap

# Bridge para LAN Local (VLAN 200)
/interface bridge add name=bridge-lan comment="Bridge LAN"
/interface bridge port add bridge=bridge-lan interface=ether6-lan
/interface bridge port add bridge=bridge-lan interface=ether7-gerencia

# ============================================================================
# FASE 4: Configuración de IP - ISP 1 (DHCP)
# ============================================================================

/ip dhcp-client add interface=bridge-isp1 disabled=no comment="DHCP ISP 1"

# ============================================================================
# FASE 5: Configuración de IP - ISP 2 (DHCP)
# ============================================================================

/ip dhcp-client add interface=bridge-isp2 disabled=no comment="DHCP ISP 2"

# ============================================================================
# FASE 6: Configuración de Direcciones Locales
# ============================================================================

# IP local para gerencia (router)
/ip address add address=192.168.88.1/24 interface=bridge-lan comment="Gerencia Router"

# IP para APs
/ip address add address=192.168.100.1/24 interface=bridge-aps comment="Red APs"

# ============================================================================
# FASE 7: Rutas Estáticas y Balanceo de Carga
# ============================================================================

# Esto se ejecutará después de que DHCP asigne IPs
# Las rutas se configurarán dinámicamente basadas en las IPs que obtengan los ISPs
# Inicialmente agregamos una ruta por defecto que apunte a la primera WAN

# La tabla de enrutamiento se configurará después de obtener IPs de DHCP
/ip route add dst-address=0.0.0.0/0 gateway=bridge-isp1 comment="Ruta default ISP1"
/ip route add dst-address=0.0.0.0/0 gateway=bridge-isp2 comment="Ruta default ISP2"

# ============================================================================
# FASE 8: DHCP Server para APs
# ============================================================================

/ip pool add name=pool-aps ranges=192.168.100.2-192.168.100.254

/ip dhcp-server add address-pool=pool-aps interface=bridge-aps \
    name=dhcp-aps disabled=no

/ip dhcp-server network add address=192.168.100.0/24 gateway=192.168.100.1 \
    comment="Network APs"

# ============================================================================
# FASE 9: DHCP Server para LAN
# ============================================================================

/ip pool add name=pool-lan ranges=192.168.88.10-192.168.88.254

/ip dhcp-server add address-pool=pool-lan interface=bridge-lan \
    name=dhcp-lan disabled=no

/ip dhcp-server network add address=192.168.88.0/24 gateway=192.168.88.1 \
    comment="Network LAN"

# ============================================================================
# FASE 10: Configuración de Firewall - Rules de Entrada
# ============================================================================

# Aceptar conexiones establecidas
/ip firewall filter add action=accept chain=input connection-state=established,related \
    comment="Accept established/related"

# Aceptar acceso local
/ip firewall filter add action=accept chain=input src-address=192.168.0.0/16 \
    comment="Accept local networks"

# Aceptar loopback
/ip firewall filter add action=accept chain=input src-address=127.0.0.1 \
    comment="Accept loopback"

# ICMP (ping)
/ip firewall filter add action=accept chain=input protocol=icmp \
    comment="Accept ICMP"

# SSH desde redes locales solo
/ip firewall filter add action=accept chain=input protocol=tcp dst-port=22 \
    src-address=192.168.0.0/16 comment="Accept SSH from local"

# Bloquear SSH desde WAN
/ip firewall filter add action=drop chain=input protocol=tcp dst-port=22 \
    comment="Drop SSH from WAN"

# REST API solo desde local
/ip firewall filter add action=accept chain=input protocol=tcp dst-port=80 \
    src-address=192.168.0.0/16 comment="Accept HTTP from local"

# Bloquear todo lo demás
/ip firewall filter add action=drop chain=input comment="Drop all else"

# ============================================================================
# FASE 11: Configuración de Firewall - Forward
# ============================================================================

# Aceptar forward establecido
/ip firewall filter add action=accept chain=forward connection-state=established,related \
    comment="Accept established forward"

# NAT para ISP 1
/ip firewall nat add action=masquerade chain=srcnat out-interface=bridge-isp1 \
    comment="NAT for ISP1"

# NAT para ISP 2
/ip firewall nat add action=masquerade chain=srcnat out-interface=bridge-isp2 \
    comment="NAT for ISP2"

# Aceptar tráfico desde APs
/ip firewall filter add action=accept chain=forward src-address=192.168.100.0/24 \
    comment="Accept from APs"

# Aceptar tráfico desde LAN
/ip firewall filter add action=accept chain=forward src-address=192.168.88.0/24 \
    comment="Accept from LAN"

# Bloquear forward lo demás
/ip firewall filter add action=drop chain=forward comment="Drop other forward"

# ============================================================================
# FASE 12: Habilitar REST API
# ============================================================================

/ip service enable rest
/ip service set rest port=80

# ============================================================================
# FASE 13: Crear usuario API
# ============================================================================

/user add name=api-container password=NAC_MikroTik_2025 group=write disabled=no \
    comment="API user for NAC System"

# ============================================================================
# FASE 14: Configuración de Identidad
# ============================================================================

/system identity set name=MikroTik-NAC-Dual-ISP

# ============================================================================
# FASE 15: DNS Estático
# ============================================================================

/ip dns set allow-remote-requests=yes servers=8.8.8.8,8.8.4.4 cache-size=2048

# ============================================================================
# FASE 16: NTP (Sincronización de Tiempo)
# ============================================================================

/system ntp client set enabled=yes servers=0.pool.ntp.org

# ============================================================================
# CONFIGURACIÓN MANUAL REQUERIDA (después de este script)
# ============================================================================

# 1. Esperar 30 segundos a que DHCP asigne IPs a ISP1 e ISP2
#
# 2. Ver IPs asignadas:
#    /ip address print
#
# 3. Configurar rutas con pesos para balanceo:
#    /ip route print
#
# 4. Ejemplo de balanceo con PCC (Per Connection Classifier):
#    /ip firewall mangle add chain=prerouting dst-address-type=!local \
#        new-routing-mark=isp1 passthrough=yes per-connection-classifier=both-addresses-and-ports:2/0
#    /ip firewall mangle add chain=prerouting dst-address-type=!local \
#        new-routing-mark=isp2 passthrough=yes per-connection-classifier=both-addresses-and-ports:2/1
#
#    /ip route add dst-address=0.0.0.0/0 gateway=<IP_ISP1> routing-mark=isp1 comment="Route ISP1"
#    /ip route add dst-address=0.0.0.0/0 gateway=<IP_ISP2> routing-mark=isp2 comment="Route ISP2"

# ============================================================================
# ANOTACIONES FINALES
# ============================================================================

# Puerto 1 (ether1-isp1): ISP 1 - DHCP
# Puerto 2 (ether2-isp2): ISP 2 - DHCP
# Puerto 3 (ether3-ap): Access Point 1 - Red 192.168.100.0/24
# Puerto 4 (ether4-ap): Access Point 2 - Red 192.168.100.0/24
# Puerto 5 (ether5-ap): Access Point 3 - Red 192.168.100.0/24
# Puerto 6 (ether6-lan): LAN Local - Red 192.168.88.0/24
# Puerto 7 (ether7-gerencia): Gerencia/NAC - Red 192.168.88.0/24
# WiFi 5GHz: VLAN 50 (si aplica)
# WiFi 2.4GHz: VLAN 51 (si aplica)
