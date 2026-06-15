#!/usr/bin/env python3
"""
Script de validación de configuración del router MikroTik.
Verifica que todos los componentes están configurados correctamente para NAC.
Uso: python validate_router.py
"""

import sys
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
import json
import base64

class RouterValidator:
    def __init__(self, host="192.168.88.1", port=80, username="api-container", password="NAC_MikroTik_2025"):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.base_url = f"http://{host}:{port}/rest"
        self.results = []

    def _request(self, endpoint):
        """Realiza una petición HTTP a la REST API"""
        url = f"{self.base_url}{endpoint}"
        credentials = f"{self.username}:{self.password}"
        base64_credentials = base64.b64encode(credentials.encode()).decode()

        headers = {
            "Authorization": f"Basic {base64_credentials}",
            "Content-Type": "application/json"
        }

        try:
            request = Request(url, headers=headers)
            response = urlopen(request, timeout=5)
            data = response.read().decode()
            return json.loads(data) if data else {}
        except HTTPError as e:
            raise Exception(f"HTTP {e.code}: {e.reason}")
        except URLError as e:
            raise Exception(f"Connection error: {e.reason}")
        except Exception as e:
            raise Exception(str(e))

    def test(self, name, endpoint, expected_key=None):
        """Realiza un test y registra el resultado"""
        try:
            result = self._request(endpoint)
            self.results.append((name, True, result if isinstance(result, dict) else {"data": result}))
            return True
        except Exception as e:
            self.results.append((name, False, str(e)))
            return False

    def run(self):
        """Ejecuta todos los tests de validación"""
        print("\n" + "="*70)
        print("Validador de Configuración — MikroTik NAC")
        print("="*70 + "\n")

        print(f"[*] Conectando a: {self.host}:{self.port}")
        print(f"[*] Usuario: {self.username}\n")

        # Test 1: Conectividad básica
        print("[TEST 1] Conectividad básica...")
        if not self.test("System Identity", "/system/identity"):
            print("✗ No se puede conectar al router")
            self._print_results()
            return False
        print("✓ REST API accesible\n")

        # Test 2: Address-lists
        print("[TEST 2] Verificando address-lists...")
        try:
            lists = self._request("/ip/firewall/address-list")
            whitelist_count = sum(1 for item in lists if item.get("list") == "mac-whitelist")
            blocklist_count = sum(1 for item in lists if item.get("list") == "mac-blocked")

            if whitelist_count > 0:
                print(f"✓ MAC whitelist encontrada ({whitelist_count} entries)")
            else:
                print("✗ MAC whitelist no encontrada")

            if blocklist_count > 0:
                print(f"✓ MAC blocklist encontrada ({blocklist_count} entries)")
            else:
                print("✗ MAC blocklist no encontrada")
        except Exception as e:
            print(f"✗ Error leyendo address-lists: {e}")
        print()

        # Test 3: Firewall rules
        print("[TEST 3] Verificando firewall rules...")
        try:
            rules = self._request("/ip/firewall/filter")
            forward_rules = [r for r in rules if r.get("chain") == "forward"]
            print(f"✓ Firewall rules encontradas ({len(forward_rules)} forward rules)")
            for i, rule in enumerate(forward_rules[:3]):
                comment = rule.get("comment", "sin comentario")
                print(f"  Regla {i}: {comment}")
        except Exception as e:
            print(f"✗ Error leyendo firewall rules: {e}")
        print()

        # Test 4: Wireless
        print("[TEST 4] Verificando configuración wireless...")
        try:
            interfaces = self._request("/interface/wireless")
            if interfaces:
                for iface in interfaces:
                    ssid = iface.get("ssid", "N/A")
                    disabled = iface.get("disabled", True)
                    status = "HABILITADA" if not disabled else "DESHABILITADA"
                    print(f"✓ Interfaz wireless: '{ssid}' ({status})")
                    if ssid == "DS-1405-PDVSA":
                        print("  ✓ SSID correcto para NAC")
            else:
                print("✗ No se encontraron interfaces wireless")
        except Exception as e:
            print(f"✗ Error leyendo wireless: {e}")
        print()

        # Test 5: DHCP Server
        print("[TEST 5] Verificando DHCP server...")
        try:
            dhcp_servers = self._request("/ip/dhcp-server")
            if dhcp_servers:
                for server in dhcp_servers:
                    interface = server.get("interface", "N/A")
                    disabled = server.get("disabled", True)
                    status = "ACTIVO" if not disabled else "INACTIVO"
                    print(f"✓ DHCP server en {interface} ({status})")
            else:
                print("✗ No se encontró DHCP server")
        except Exception as e:
            print(f"✗ Error leyendo DHCP: {e}")
        print()

        # Test 6: DHCP Leases
        print("[TEST 6] Verificando DHCP leases (dispositivos conectados)...")
        try:
            leases = self._request("/ip/dhcp-server/lease")
            print(f"✓ Dispositivos con IP asignada: {len(leases)}")
            for lease in leases[:5]:
                mac = lease.get("mac-address", "N/A")
                ip = lease.get("address", "N/A")
                print(f"  - {mac} → {ip}")
            if len(leases) > 5:
                print(f"  ... y {len(leases) - 5} más")
        except Exception as e:
            print(f"✗ Error leyendo DHCP leases: {e}")
        print()

        # Test 7: ARP Table
        print("[TEST 7] Verificando tabla ARP (dispositivos visibles)...")
        try:
            arp_entries = self._request("/ip/arp")
            print(f"✓ Dispositivos en red: {len(arp_entries)}")
            for entry in arp_entries[:5]:
                mac = entry.get("mac-address", "N/A")
                ip = entry.get("address", "N/A")
                iface = entry.get("interface", "N/A")
                print(f"  - {mac} ({ip}) en {iface}")
            if len(arp_entries) > 5:
                print(f"  ... y {len(arp_entries) - 5} más")
        except Exception as e:
            print(f"✗ Error leyendo ARP: {e}")
        print()

        # Test 8: Simple Queues
        print("[TEST 8] Verificando Simple Queues...")
        try:
            queues = self._request("/queue/simple")
            print(f"✓ Simple Queues activas: {len(queues)}")
            if queues:
                for queue in queues[:3]:
                    name = queue.get("name", "N/A")
                    target = queue.get("target", "N/A")
                    print(f"  - {name} para {target}")
        except Exception as e:
            print(f"✗ Error leyendo queues: {e}")
        print()

        # Test 9: DNS Static
        print("[TEST 9] Verificando DNS estáticas...")
        try:
            dns_entries = self._request("/ip/dns/static")
            print(f"✓ Entradas DNS estáticas: {len(dns_entries)}")
            if dns_entries:
                for entry in dns_entries[:3]:
                    name = entry.get("name", "N/A")
                    address = entry.get("address", "N/A")
                    print(f"  - {name} → {address}")
        except Exception as e:
            print(f"✗ Error leyendo DNS: {e}")
        print()

        # Test 10: REST API Service
        print("[TEST 10] Verificando servicio REST API...")
        try:
            services = self._request("/ip/service")
            rest_service = next((s for s in services if s.get("name") == "rest"), None)
            if rest_service:
                disabled = rest_service.get("disabled", True)
                port = rest_service.get("port", "N/A")
                status = "ACTIVA" if not disabled else "INACTIVA"
                print(f"✓ REST API en puerto {port} ({status})")
            else:
                print("✗ REST API no encontrada")
        except Exception as e:
            print(f"✗ Error leyendo servicios: {e}")
        print()

        self._print_results()
        return True

    def _print_results(self):
        """Imprime resumen de resultados"""
        print("="*70)
        print("RESUMEN")
        print("="*70)

        success_count = sum(1 for _, success, _ in self.results if success)
        total_count = len(self.results)

        print(f"\nTests exitosos: {success_count}/{total_count}\n")

        for name, success, data in self.results:
            status = "✓" if success else "✗"
            print(f"{status} {name}")
            if not success:
                print(f"  Error: {data}")

        print("\n" + "="*70)
        if success_count == total_count:
            print("✓ CONFIGURACIÓN VÁLIDA - El router está listo para NAC")
        else:
            print(f"⚠ {total_count - success_count} test(s) fallaron")
            print("Ejecuta 'python configure_router.py' para aplicar la configuración")
        print("="*70 + "\n")


if __name__ == "__main__":
    validator = RouterValidator()
    success = validator.run()
    sys.exit(0 if success else 1)
