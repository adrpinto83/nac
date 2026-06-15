# Script de Configuración Inicial - MikroTik NAC System
# Puerto 1,2: ISP1, ISP2 (WAN)
# Puerto 5: Admin local (192.168.88.5)
# Puertos 3,4,6: Access Points (DHCP)

# ============ LIMPIEZA ============
/interface bridge remove [find]
/ip address remove [find]
/ip firewall nat remove [find]
/ip firewall filter remove [find]
/ip dhcp-client remove [find]
/ip dhcp-server remove [find]
/ip dhcp-server network remove [find]

# ============ INTERFACES ============
# Puerto 1: ISP1 (DHCP)
/interface ethernet set ether1 name=ether1-isp1
/ip dhcp-client add interface=ether1-isp1 disabled=no

# Puerto 2: ISP2 (DHCP)
/interface ethernet set ether2 name=ether2-isp2
/ip dhcp-client add interface=ether2-isp2 disabled=no

# Puerto 5: Admin (IP estática)
/interface ethernet set ether5 name=ether5-admin
/ip address add address=192.168.88.5/24 interface=ether5-admin

# Puertos 3,4,6: Access Points (Bridge)
/interface bridge add name=bridge-aps
/interface bridge port add bridge=bridge-aps interface=ether3
/interface bridge port add bridge=bridge-aps interface=ether4
/interface bridge port add bridge=bridge-aps interface=ether6
/ip address add address=192.168.88.1/24 interface=bridge-aps

# ============ DHCP SERVER ============
/ip dhcp-server add name=dhcp-aps interface=bridge-aps disabled=no
/ip dhcp-server network add address=192.168.88.0/24 gateway=192.168.88.1 dns-server=8.8.8.8,8.8.4.4

# ============ DNS ============
/ip dns set servers=8.8.8.8,8.8.4.4

# ============ NAT ============
# ISP1
/ip firewall nat add chain=srcnat out-interface=ether1-isp1 action=masquerade

# ISP2
/ip firewall nat add chain=srcnat out-interface=ether2-isp2 action=masquerade

# Admin
/ip firewall nat add chain=srcnat out-interface=ether5-admin action=masquerade

# ============ FIREWALL ============
/ip firewall filter add chain=forward action=accept connection-state=established,related
/ip firewall filter add chain=forward action=drop connection-state=invalid

# ============ GUARDAR ============
/system save
