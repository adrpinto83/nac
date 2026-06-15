#!/usr/bin/env python3
"""
Test script para verificar la conexión con MikroTik RouterOS
"""

import asyncio
import sys
from routeros_client import RouterOSClient

async def test_router_connection():
    """Test la conexión con el router"""
    print("\n" + "="*70)
    print("Test de Conexión - MikroTik RouterOS")
    print("="*70 + "\n")

    # Crear cliente con configuración por defecto
    client = RouterOSClient()

    print(f"[*] Intentando conectar a: {client.host}:{client.port}")
    print(f"[*] Usuario: {client.username}")
    print(f"[*] Base URL: {client.base_url}")

    try:
        # Conectar
        print("\n[*] Conectando...")
        await client.connect()
        print("✓ Cliente HTTP creado correctamente")

        # Test de conexión
        print("\n[*] Realizando test de conexión...")
        result = await client.test_connection()

        if result:
            print("✓ ¡Conexión exitosa!")
            print("\n[*] Obteniendo información del sistema...")

            try:
                # Obtener identidad del router
                system_info = await client._request("GET", "/system/identity")
                print(f"✓ Identidad del router: {system_info}")

                # Obtener tabla ARP
                print("\n[*] Obteniendo tabla ARP...")
                arp_table = await client.get_arp_table()
                print(f"✓ Dispositivos activos encontrados: {len(arp_table)}")
                for entry in arp_table[:5]:  # Mostrar los primeros 5
                    print(f"   - MAC: {entry['mac']}, IP: {entry['ip']}, Interfaz: {entry['interface']}")
                if len(arp_table) > 5:
                    print(f"   ... y {len(arp_table) - 5} más")

            except Exception as e:
                print(f"⚠ Error obteniendo información adicional: {e}")
        else:
            print("✗ Conexión fallida")
            print("\nPosibles causas:")
            print("  1. El router no está accesible en 127.0.0.1:443")
            print("  2. Las credenciales son incorrectas")
            print("  3. El servicio REST API no está activo en el router")

    except Exception as e:
        print(f"✗ Error: {e}")
        print("\nPosibles causas:")
        print("  1. El router no está accesible")
        print("  2. Error de red o firewall bloqueando la conexión")
        print("  3. Certificado SSL autofirmado no reconocido")
        return False

    finally:
        print("\n[*] Cerrando conexión...")
        await client.disconnect()
        print("✓ Conexión cerrada")

    print("\n" + "="*70 + "\n")
    return True

async def test_custom_host(host: str, port: int = 443, username: str = "api-container", password: str = "NAC_MikroTik_2025"):
    """Test con host personalizado"""
    print(f"\n[*] Testeando host personalizado: {host}:{port}")

    client = RouterOSClient(host=host, port=port, username=username, password=password)

    try:
        await client.connect()
        result = await client.test_connection()

        if result:
            print(f"✓ Conexión a {host} exitosa")
            return True
        else:
            print(f"✗ Conexión a {host} fallida")
            return False

    except Exception as e:
        print(f"✗ Error conectando a {host}: {e}")
        return False

    finally:
        await client.disconnect()

if __name__ == "__main__":
    print("\n>>> Iniciando tests de conexión a MikroTik RouterOS")

    # Test 1: Conexión por defecto (127.0.0.1)
    print("\n" + "-"*70)
    print("TEST 1: Conexión a host por defecto (127.0.0.1:443)")
    print("-"*70)
    success = asyncio.run(test_router_connection())

    # Test 2: Intenta con IP common del router MikroTik (192.168.88.1)
    print("\n" + "-"*70)
    print("TEST 2: Intentando conexión a IP común de MikroTik (192.168.88.1:443)")
    print("-"*70)
    asyncio.run(test_custom_host("192.168.88.1"))

    print("\n>>> Tests completados")
    sys.exit(0 if success else 1)
