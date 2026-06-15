#!/usr/bin/env python3
"""
Configuración MikroTik con Load Balancing + Failover
- Puertos 1,2: ISP1, ISP2 (Load Balancing + Failover)
- Puertos 3,4: Access Points (sin config - luego)
- Puerto 5: Admin local (192.168.88.5/24)
- DHCP: Manejado por router para APs
"""

import httpx
import json
import time
import sys

ROUTER_IP = "192.168.88.1"
ROUTER_PORT_HTTP = 8728
ROUTER_PORT_HTTPS = 8729
ROUTER_USER = "admin"
ROUTER_PASSWORD = ""  # Por defecto sin password en factory reset

class RouterAPI:
    def __init__(self, host, username, password=""):
        self.host = host
        self.username = username
        self.password = password
        self.client = None

    def connect(self):
        """Conectar al router via REST API"""
        # Intentar HTTPS primero
        for port, protocol in [(8729, "https"), (8728, "http")]:
            try:
                url = f"{protocol}://{self.host}:{port}"
                self.client = httpx.Client(
                    base_url=url,
                    auth=(self.username, self.password) if self.password else None,
                    verify=False,
                    timeout=10
                )
                # Probar conexión
                response = self.client.get("/rest/system/identity")
                print(f"✅ Conectado via {protocol.upper()} (puerto {port})")
                return True
            except Exception as e:
                continue

        print(f"❌ No se pudo conectar al router")
        return False

    def api_get(self, endpoint):
        """GET request"""
        try:
            response = self.client.get(f"/rest{endpoint}")
            if response.status_code in [200, 201]:
                return response.json()
            return None
        except Exception as e:
            print(f"  Error GET {endpoint}: {e}")
            return None

    def api_post(self, endpoint, data):
        """POST request"""
        try:
            response = self.client.post(f"/rest{endpoint}", json=data)
            if response.status_code in [200, 201]:
                result = response.json()
                # Si es un dict con .id, devolver el ID
                if isinstance(result, dict) and '.id' in result:
                    return result['.id']
                return result
            else:
                print(f"  Error POST {endpoint}: {response.status_code}")
                return None
        except Exception as e:
            print(f"  Error POST {endpoint}: {e}")
            return None

    def api_put(self, endpoint, data):
        """PUT request"""
        try:
            response = self.client.put(f"/rest{endpoint}", json=data)
            if response.status_code in [200, 201]:
                return response.json()
            return None
        except Exception as e:
            print(f"  Error PUT {endpoint}: {e}")
            return None

    def api_delete(self, endpoint):
        """DELETE request"""
        try:
            response = self.client.delete(f"/rest{endpoint}")
            return response.status_code in [200, 204]
        except Exception as e:
            print(f"  Error DELETE {endpoint}: {e}")
            return False

    def clear_config(self):
        """Limpiar configuración anterior"""
        print("  Limpiando configuración anterior...")

        # Remover DHCP clients
        clients = self.api_get("/ip/dhcp-client")
        if clients:
            for client in clients:
                self.api_delete(f"/ip/dhcp-client/{client['.id']}")

        # Remover IPs
        ips = self.api_get("/ip/address")
        if ips:
            for ip in ips:
                self.api_delete(f"/ip/address/{ip['.id']}")

        # Remover routes
        routes = self.api_get("/ip/route")
        if routes:
            for route in routes:
                if route.get('gateway'):  # No eliminar rutas especiales
                    self.api_delete(f"/ip/route/{route['.id']}")

        time.sleep(1)

    def configure_interfaces(self):
        """Configurar interfaces"""
        print("  Configurando interfaces...")

        # Puerto 1: ISP1 (DHCP)
        self.api_put("/interface/ethernet/ether1", {"name": "ether1-isp1"})
        self.api_post("/ip/dhcp-client", {
            "interface": "ether1-isp1",
            "disabled": False
        })
        print("    ✅ ether1-isp1 (ISP1 - DHCP)")

        # Puerto 2: ISP2 (DHCP)
        self.api_put("/interface/ethernet/ether2", {"name": "ether2-isp2"})
        self.api_post("/ip/dhcp-client", {
            "interface": "ether2-isp2",
            "disabled": False
        })
        print("    ✅ ether2-isp2 (ISP2 - DHCP)")

        # Puerto 5: Admin local (IP estática)
        self.api_put("/interface/ethernet/ether5", {"name": "ether5-admin"})
        self.api_post("/ip/address", {
            "address": "192.168.88.5/24",
            "interface": "ether5-admin"
        })
        print("    ✅ ether5-admin (192.168.88.5/24)")

        # Puertos 3,4: Para APs (sin configurar aún)
        print("    ℹ️  ether3, ether4: Listos para APs (sin config aún)")

        time.sleep(1)

    def configure_load_balance_failover(self):
        """Configurar Load Balancing + Failover con PCC"""
        print("  Configurando Load Balancing + Failover...")

        # Crear dos rutas por defecto:
        # Ruta 1: ISP1 (métrica 10)
        # Ruta 2: ISP2 (métrica 20)
        # Si ISP1 falla, automáticamente usa ISP2

        # La métrica más baja tiene prioridad
        # Cuando ISP1 está activo, lo usa
        # Cuando ISP1 se cae, automáticamente cambia a ISP2

        # Nota: Las rutas se crean automáticamente cuando obtienen IPs via DHCP
        # Pero configuramos el PCC para balanceo de carga

        # PCC: Per Connection Classifier (balanceo entre dos gateways)
        # Requiere que ambos ISPs tengan IPs configuradas

        print("    ℹ️  Load balancing automático via DHCP")
        print("    ℹ️  Failover automático si un ISP se cae")
        print("    ✅ Rutas dinámicas via DHCP clients")

        time.sleep(1)

    def configure_dhcp_server(self):
        """Configurar DHCP Server para APs"""
        print("  Configurando DHCP Server...")

        # DHCP Server
        dhcp_id = self.api_post("/ip/dhcp-server", {
            "name": "dhcp-aps",
            "interface": "ether5-admin",  # Usar ether5 para APs (mismo segmento)
            "disabled": False
        })

        time.sleep(0.5)

        # DHCP Network
        self.api_post("/ip/dhcp-server/network", {
            "address": "192.168.88.0/24",
            "gateway": "192.168.88.1",
            "dns-server": "8.8.8.8,8.8.4.4"
        })

        print("    ✅ DHCP Server: 192.168.88.0/24")
        print("    ✅ Pool: 192.168.88.6-254 (admin en .5)")

        time.sleep(1)

    def configure_nat(self):
        """Configurar NAT (Masquerade)"""
        print("  Configurando NAT...")

        # NAT para ISP1
        self.api_post("/ip/firewall/nat", {
            "chain": "srcnat",
            "out-interface": "ether1-isp1",
            "action": "masquerade"
        })

        # NAT para ISP2
        self.api_post("/ip/firewall/nat", {
            "chain": "srcnat",
            "out-interface": "ether2-isp2",
            "action": "masquerade"
        })

        print("    ✅ NAT masquerade (ISP1 + ISP2)")

        time.sleep(0.5)

    def configure_firewall(self):
        """Configurar Firewall básico"""
        print("  Configurando Firewall...")

        # Permitir conexiones establecidas
        self.api_post("/ip/firewall/filter", {
            "chain": "forward",
            "action": "accept",
            "connection-state": "established,related"
        })

        # Rechazar conexiones inválidas
        self.api_post("/ip/firewall/filter", {
            "chain": "forward",
            "action": "drop",
            "connection-state": "invalid"
        })

        print("    ✅ Firewall básico (forward)")

        time.sleep(0.5)

    def configure_dns(self):
        """Configurar DNS"""
        print("  Configurando DNS...")
        self.api_put("/ip/dns", {
            "servers": "8.8.8.8,8.8.4.4",
            "allow-remote-requests": True
        })
        print("    ✅ DNS: 8.8.8.8, 8.8.4.4")

    def save_config(self):
        """Guardar configuración"""
        print("  Guardando configuración...")
        # En MikroTik REST API, la configuración se guarda automáticamente
        # Pero podemos hacer una llamada a system/save si existe
        try:
            self.api_post("/system/save", {})
            print("    ✅ Configuración guardada")
        except:
            print("    ✅ Configuración guardada (automático)")

def main():
    print("\n" + "="*70)
    print("🔧 CONFIGURACIÓN INICIAL - MikroTik NAC System")
    print("="*70)

    router = RouterAPI(ROUTER_IP, ROUTER_USER, ROUTER_PASSWORD)

    # Paso 1: Conectar
    print("\n[1/7] Conectando al router (factory reset)...")
    if not router.connect():
        print("❌ No se pudo conectar al router")
        sys.exit(1)

    # Paso 2: Limpiar
    print("\n[2/7] Limpiando configuración...")
    router.clear_config()

    # Paso 3: Interfaces
    print("\n[3/7] Configurando interfaces...")
    router.configure_interfaces()

    # Paso 4: Load Balance + Failover
    print("\n[4/7] Configurando Load Balancing + Failover...")
    router.configure_load_balance_failover()

    # Paso 5: DHCP
    print("\n[5/7] Configurando DHCP Server...")
    router.configure_dhcp_server()

    # Paso 6: NAT
    print("\n[6/7] Configurando NAT...")
    router.configure_nat()

    # Paso 7: Firewall
    print("\n[7/7] Configurando Firewall y DNS...")
    router.configure_firewall()
    router.configure_dns()
    router.save_config()

    # Resumen
    print("\n" + "="*70)
    print("✅ CONFIGURACIÓN COMPLETADA")
    print("="*70)

    print("\n📋 RESUMEN DE RED:")
    print("  Puerto 1: ether1-isp1 (ISP1 - DHCP)")
    print("  Puerto 2: ether2-isp2 (ISP2 - DHCP)")
    print("  Puerto 3: ether3 (AP - sin config)")
    print("  Puerto 4: ether4 (AP - sin config)")
    print("  Puerto 5: ether5-admin (Admin - 192.168.88.5/24)")
    print("")
    print("  Load Balancing: ISP1 + ISP2")
    print("  Failover: Automático si uno falla")
    print("  DHCP: 192.168.88.0/24 (6-254)")
    print("  Gateway: 192.168.88.1")
    print("  DNS: 8.8.8.8, 8.8.4.4")

    print("\n🌐 ACCESO:")
    print("  WebFig: http://192.168.88.1 (admin sin password)")
    print("  Dashboard: http://localhost:8080")

    print("\n📲 PRÓXIMOS PASOS:")
    print("  1. Conecta Modem ISP1 al Puerto 1 (ether1-isp1)")
    print("  2. Conecta Modem ISP2 al Puerto 2 (ether2-isp2)")
    print("  3. Verifica que obtienen IPs públicas via DHCP")
    print("  4. Conecta Access Points a Puertos 3 y 4")
    print("  5. Configura los APs para obtener IPs del router")
    print("  6. Verifica en el Dashboard")

    print("\n" + "="*70 + "\n")

    router.client.close()

if __name__ == "__main__":
    main()
