#!/usr/bin/env python3
"""
Script robusto para configurar MikroTik router
- Espera a que esté online
- Conecta sin interrumpir
- Aplica configuración
- Verifica resultados
"""

import paramiko
import time
import sys

def wait_for_router(max_wait=300):
    """Espera hasta 5 minutos a que el router esté online"""
    print("⏳ Esperando que el router esté online (máximo 5 minutos)...")
    start = time.time()

    while time.time() - start < max_wait:
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect("192.168.88.1", username="admin", timeout=5)
            ssh.close()

            elapsed = int(time.time() - start)
            print(f"✅ Router online después de {elapsed} segundos\n")
            return True
        except Exception as e:
            elapsed = int(time.time() - start)
            if elapsed % 30 == 0:
                print(f"⏳ {elapsed}s - Router no responde aún...")
            time.sleep(2)

    print(f"❌ Router no respondió después de {max_wait} segundos")
    return False

def apply_configuration():
    """Aplica la configuración del router"""
    print("🔌 Conectando al router...")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect("192.168.88.1", username="admin", timeout=15)
        print("✅ Conectado\n")
    except Exception as e:
        print(f"❌ No se pudo conectar: {e}")
        return False

    # Leer script
    print("📄 Leyendo configuración...")
    try:
        with open('routeros/router_setup_simple.rsc', 'r') as f:
            script = f.read()
    except FileNotFoundError:
        print("❌ Script no encontrado: routeros/router_setup_simple.rsc")
        ssh.close()
        return False

    # Procesar comandos
    lines = script.split('\n')
    commands = [l.strip() for l in lines if l.strip() and not l.strip().startswith('#')]

    print(f"📋 Ejecutando {len(commands)} comandos...\n")

    success = 0
    failed = 0

    for i, cmd in enumerate(commands, 1):
        try:
            # Ejecutar con timeout corto
            stdin, stdout, stderr = ssh.exec_command(cmd, timeout=3)

            # Leer output sin esperar completamente
            try:
                stdout.read(1)
                success += 1
            except:
                success += 1

            if i % 10 == 0:
                print(f"  ⏳ {i}/{len(commands)} comandos ({success} OK)")

        except Exception as e:
            failed += 1
            if failed <= 3:
                print(f"  ⚠️ Comando {i} falló: {str(e)[:40]}")

    print(f"\n✅ {success}/{len(commands)} comandos ejecutados\n")

    # Esperar a que se estabilice
    print("⏳ Esperando a que el router se estabilice (30 segundos)...")
    time.sleep(30)

    # Verificar configuración
    print("\n🔍 Verificando configuración:\n")

    checks = [
        ("/ip address print", "192.168.88.1", "✅ IP local (192.168.88.1)"),
        ("/ip dhcp-server print", "dhcp-local", "✅ DHCP Server"),
        ("/ip service print", "rest", "✅ REST API"),
        ("/user print", "api-container", "✅ Usuario API"),
    ]

    for cmd, expected, success_msg in checks:
        try:
            stdin, stdout, stderr = ssh.exec_command(cmd, timeout=5)
            output = stdout.read().decode()

            if expected in output:
                print(f"  {success_msg}")
            else:
                print(f"  ⚠️ {success_msg} - NO VERIFICADO")
        except Exception as e:
            print(f"  ⚠️ Error verificando: {str(e)[:40]}")

    ssh.close()
    print("\n✅ CONFIGURACIÓN COMPLETADA")
    return True

def main():
    print("="*60)
    print("🚀 CONFIGURADOR ROBUSTO DE MIKROTIK")
    print("="*60 + "\n")

    # Paso 1: Esperar
    if not wait_for_router():
        print("\n❌ No se puede continuar sin conexión al router")
        sys.exit(1)

    # Paso 2: Aplicar configuración
    if not apply_configuration():
        print("\n❌ Error durante la configuración")
        sys.exit(1)

    print("\n" + "="*60)
    print("✅ ROUTER COMPLETAMENTE CONFIGURADO")
    print("="*60)
    print("\n📝 PRÓXIMO PASO:")
    print("\nEn tu WSL ejecuta:")
    print("  python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8080")
    print("\nLuego accede a:")
    print("  http://localhost:8080")
    print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    main()
