#!/usr/bin/env python3
"""
Script de diagnóstico para identificar problemas con el router.
"""

import sys
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
import json
import base64

def test_endpoint(host, port, username, password, endpoint):
    """Intenta conectar con credenciales específicas"""
    url = f"http://{host}:{port}/rest{endpoint}"
    credentials = f"{username}:{password}"
    base64_credentials = base64.b64encode(credentials.encode()).decode()

    headers = {
        "Authorization": f"Basic {base64_credentials}",
        "Content-Type": "application/json"
    }

    try:
        request = Request(url, headers=headers)
        response = urlopen(request, timeout=5)
        data = response.read().decode()
        return response.status, json.loads(data) if data else {}
    except HTTPError as e:
        return e.code, {"error": f"HTTP {e.code}: {e.reason}"}
    except Exception as e:
        return None, {"error": str(e)}

print("\n" + "="*70)
print("DIAGNÓSTICO DEL ROUTER MIKROTIK")
print("="*70 + "\n")

host = "192.168.88.1"
port = 80

# Test 1: Admin sin contraseña
print("[TEST 1] Conectando como admin (sin contraseña)...")
status, result = test_endpoint(host, port, "admin", "", "/system/identity")
print(f"  Status: {status}")
if status == 200:
    print(f"  ✓ ÉXITO: {result}")
else:
    print(f"  ✗ Falló: {result}")

# Test 2: Admin con contraseña vacía
print("\n[TEST 2] Conectando como admin (contraseña='admin')...")
status, result = test_endpoint(host, port, "admin", "admin", "/system/identity")
print(f"  Status: {status}")
if status == 200:
    print(f"  ✓ ÉXITO: {result}")
else:
    print(f"  ✗ Falló: {result}")

# Test 3: api-container con contraseña esperada
print("\n[TEST 3] Conectando como api-container (NAC_MikroTik_2025)...")
status, result = test_endpoint(host, port, "api-container", "NAC_MikroTik_2025", "/system/identity")
print(f"  Status: {status}")
if status == 200:
    print(f"  ✓ ÉXITO: {result}")
else:
    print(f"  ✗ Falló: {result}")

# Test 4: Verificar usuarios del router (via admin)
print("\n[TEST 4] Listando usuarios del router (como admin)...")
status, result = test_endpoint(host, port, "admin", "", "/user")
print(f"  Status: {status}")
if status == 200:
    print(f"  ✓ Usuarios encontrados:")
    for user in result:
        print(f"    - {user.get('name')} (grupo: {user.get('group')})")
else:
    print(f"  ✗ No se pueden leer usuarios: {result}")

# Test 5: Verificar servicios REST
print("\n[TEST 5] Verificando servicio REST API...")
status, result = test_endpoint(host, port, "admin", "", "/ip/service")
print(f"  Status: {status}")
if status == 200:
    print(f"  ✓ Servicios:")
    for service in result:
        if service.get('name') == 'rest':
            disabled = service.get('disabled', True)
            port_num = service.get('port', 'N/A')
            print(f"    REST API: disabled={disabled}, port={port_num}")
else:
    print(f"  ✗ No se pueden leer servicios: {result}")

print("\n" + "="*70)
print("FIN DE DIAGNÓSTICO")
print("="*70 + "\n")
