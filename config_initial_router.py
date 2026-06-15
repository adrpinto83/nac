#!/usr/bin/env python3
"""
Configuración Inicial del MikroTik para NAC System
- Puerto 1,2: ISP1, ISP2 (WAN con DHCP)
- Puerto 5: Admin local (192.168.88.5) + Internet
- Puertos 3,4,6: Access Points (DHCP 192.168.88.100-200)
"""

import paramiko
import time
import sys

ROUTER_IP = "192.168.88.1"
ROUTER_USER = "admin"
ROUTER_PASSWORD = "NAC_MikroTik_2025"

def ssh_command(ssh, command):
    """Ejecuta comando en router"""
    stdin, stdout, stderr = ssh.exec_command(command)
    return stdout.read().decode('utf-8', errors='ignore')

def main():
    print("\n" + "="*70)
    print("🔧 CONFIGURACIÓN INICIAL - MikroTik NAC System")
    print("="*70)

    try:
        # Conectar
        print("\n[1/5] Conectando al router...")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ROUTER_IP, username=ROUTER_USER, password=ROUTER_PASSWORD, timeout=10)
        print("    ✅ Conectado")

        # Hacer backup
        print("\n[2/5] Haciendo backup de configuración actual...")
        ssh_command(ssh, '/system backup save name=backup_before_nac')
        print("    ✅ Backup guardado como: backup_before_nac.backup")

        # Limpiar configuración anterior
        print("\n[3/5] Limpiando configuración anterior...")

        # Remover interfaces y configuraciones viejas
        ssh_command(ssh, '/interface bridge remove [find]')
        ssh_command(ssh, '/ip address remove [find]')
        ssh_command(ssh, '/ip firewall nat remove [find]')
        ssh_command(ssh, '/ip firewall filter remove [find]')
        ssh_command(ssh, '/ip dhcp-server remove [find]')
        ssh_command(ssh, '/ip dhcp-server network remove [find]')
        print("    ✅ Configuración limpia")

        time.sleep(1)

        # Configurar interfaces
        print("\n[4/5] Configurando interfaces...")

        # Puerto 1: ISP1 (DHCP)
        ssh_command(ssh, '/interface ethernet set ether1 name=ether1-isp1')
        ssh_command(ssh, '/ip dhcp-client add interface=ether1-isp1 disabled=no')
        print("    ✅ ether1-isp1: ISP1 (DHCP)")

        # Puerto 2: ISP2 (DHCP)
        ssh_command(ssh, '/interface ethernet set ether2 name=ether2-isp2')
        ssh_command(ssh, '/ip dhcp-client add interface=ether2-isp2 disabled=no')
        print("    ✅ ether2-isp2: ISP2 (DHCP)")

        # Puerto 5: Admin (IP estática + puente a ISP)
        ssh_command(ssh, '/interface ethernet set ether5 name=ether5-admin')
        ssh_command(ssh, '/ip address add address=192.168.88.5/24 interface=ether5-admin')
        print("    ✅ ether5-admin: 192.168.88.5/24")

        # Puertos 3,4,6: Access Points (Bridge)
        ssh_command(ssh, '/interface bridge add name=bridge-aps')
        ssh_command(ssh, '/interface bridge port add bridge=bridge-aps interface=ether3')
        ssh_command(ssh, '/interface bridge port add bridge=bridge-aps interface=ether4')
        ssh_command(ssh, '/interface bridge port add bridge=bridge-aps interface=ether6')
        ssh_command(ssh, '/ip address add address=192.168.88.1/24 interface=bridge-aps')
        print("    ✅ bridge-aps: ether3,4,6 (DHCP server)")

        time.sleep(1)

        # Configurar DHCP Server
        print("\n[5/5] Configurando DHCP Server...")

        ssh_command(ssh, '/ip dhcp-server add name=dhcp-aps interface=bridge-aps disabled=no')
        ssh_command(ssh, '/ip dhcp-server network add address=192.168.88.0/24 gateway=192.168.88.1 dns-server=8.8.8.8,8.8.4.4')
        print("    ✅ DHCP: 192.168.88.100-200")

        # Configurar NAT
        print("\n[6/6] Configurando NAT y Firewall...")

        # NAT para ISP1
        ssh_command(ssh, '/ip firewall nat add chain=srcnat out-interface=ether1-isp1 action=masquerade')
        print("    ✅ NAT ISP1 (ether1)")

        # NAT para ISP2
        ssh_command(ssh, '/ip firewall nat add chain=srcnat out-interface=ether2-isp2 action=masquerade')
        print("    ✅ NAT ISP2 (ether2)")

        # NAT para Admin
        ssh_command(ssh, '/ip firewall nat add chain=srcnat out-interface=ether5-admin action=masquerade')
        print("    ✅ NAT Admin (ether5)")

        # Firewall básico
        ssh_command(ssh, '/ip firewall filter add chain=forward action=accept connection-state=established,related')
        ssh_command(ssh, '/ip firewall filter add chain=forward action=drop connection-state=invalid')
        print("    ✅ Firewall configurado")

        # Guardar configuración
        print("\n[✓] Guardando configuración...")
        ssh_command(ssh, '/system save')
        print("    ✅ Configuración guardada")

        print("\n" + "="*70)
        print("✅ CONFIGURACIÓN COMPLETADA")
        print("="*70)

        print("\n📋 RESUMEN DE RED:")
        print("  ISP1:        ether1-isp1 (DHCP)")
        print("  ISP2:        ether2-isp2 (DHCP)")
        print("  Admin:       ether5-admin (192.168.88.5/24)")
        print("  APs:         bridge-aps (192.168.88.1/24)")
        print("  DHCP Pool:   192.168.88.100-200")
        print("  Gateway:     192.168.88.1")
        print("  DNS:         8.8.8.8, 8.8.4.4")

        print("\n🌐 ACCESO:")
        print("  Web:         http://192.168.88.1 (router)")
        print("  Admin Local: http://192.168.88.5 (desde ether5)")
        print("  Dashboard:   http://localhost:8080 (NAC System)")

        print("\n📲 PRÓXIMOS PASOS:")
        print("  1. Conecta ISP1 al puerto 1 (ether1)")
        print("  2. Conecta ISP2 al puerto 2 (ether2)")
        print("  3. Conecta Admin PC al puerto 5 (ether5) - obtendrá 192.168.88.5-254")
        print("  4. Conecta Access Points a puertos 3,4,6")
        print("  5. Los usuarios en APs obtendrán IPs: 192.168.88.100-200")

        print("\n" + "="*70 + "\n")

        ssh.close()

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
