#!/usr/bin/env python3
"""
Script para verificar que la configuración del router fue exitosa

Verifica:
- Conectividad SSH
- Interfaces configuradas
- Bridges activos
- DHCP asignando IPs
- REST API habilitada
- Usuario API creado
"""

import sys
import os
import paramiko
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class RouterVerifier:
    def __init__(self, host, user, password):
        self.host = host
        self.user = user
        self.password = password
        self.ssh = None
        self.checks_passed = 0
        self.checks_failed = 0

    def connect(self):
        try:
            logger.info(f"🔌 Conectando a {self.host}...")
            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh.connect(self.host, username=self.user, password=self.password, timeout=10)
            logger.info("✅ Conectado\n")
            return True
        except Exception as e:
            logger.error(f"❌ Error de conexión: {e}\n")
            return False

    def execute(self, cmd):
        try:
            _, stdout, stderr = self.ssh.exec_command(cmd)
            return stdout.read().decode(), stderr.read().decode()
        except Exception as e:
            return None, str(e)

    def check(self, name, cmd, expected_strings):
        logger.info(f"🔍 {name}")
        output, error = self.execute(cmd)

        if output is None:
            logger.info(f"   ❌ Error: {error}\n")
            self.checks_failed += 1
            return False

        found = all(exp in output for exp in expected_strings)

        if found:
            logger.info(f"   ✅ OK\n")
            self.checks_passed += 1
            return True
        else:
            logger.info(f"   ⚠️  Verificar manualmente\n")
            logger.info(f"   Output: {output[:200]}\n")
            self.checks_failed += 1
            return False

    def verify_all(self):
        logger.info("=" * 60)
        logger.info("VERIFICACIÓN DE CONFIGURACIÓN DEL ROUTER")
        logger.info("=" * 60 + "\n")

        # Verificaciones básicas
        logger.info("📋 INTERFACES:\n")
        self.check("ether1-isp1 renombrada", "/interface print", ["ether1-isp1"])
        self.check("ether2-isp2 renombrada", "/interface print", ["ether2-isp2"])
        self.check("ether3-ap renombrada", "/interface print", ["ether3-ap"])
        self.check("Puertos 3-5 configurados", "/interface print", ["ether3-ap", "ether4-ap", "ether5-ap"])

        logger.info("🌉 BRIDGES:\n")
        self.check("bridge-isp1 creado", "/interface bridge print", ["bridge-isp1"])
        self.check("bridge-isp2 creado", "/interface bridge print", ["bridge-isp2"])
        self.check("bridge-aps creado", "/interface bridge print", ["bridge-aps"])
        self.check("bridge-lan creado", "/interface bridge print", ["bridge-lan"])

        logger.info("🌐 DHCP:\n")
        self.check("DHCP ISP1 activo", "/ip dhcp-client print", ["dhcp-isp1"])
        self.check("DHCP ISP2 activo", "/ip dhcp-client print", ["dhcp-isp2"])
        self.check("DHCP APs activo", "/ip dhcp-server print", ["dhcp-aps"])
        self.check("DHCP LAN activo", "/ip dhcp-server print", ["dhcp-lan"])

        logger.info("🔐 SERVICIOS:\n")
        self.check("REST API habilitada", "/ip service print", ["rest"])
        self.check("SSH disponible", "/ip service print", ["ssh"])

        logger.info("👤 USUARIOS:\n")
        self.check("Usuario api-container creado", "/user print", ["api-container"])

        logger.info("📊 DIRECCIONES IP:\n")
        output, _ = self.execute("/ip address print")
        if output:
            logger.info("   Direcciones IP configuradas:")
            for line in output.split('\n')[:10]:
                if line.strip():
                    logger.info(f"   {line}")
        logger.info("")

        logger.info("💾 DHCP CLIENTS (ISPs):\n")
        output, _ = self.execute("/ip dhcp-client print")
        if output:
            for line in output.split('\n')[:15]:
                if line.strip():
                    logger.info(f"   {line}")
        logger.info("")

        # Resumen
        logger.info("=" * 60)
        logger.info("RESUMEN")
        logger.info("=" * 60)
        logger.info(f"✅ Verificaciones pasadas: {self.checks_passed}")
        logger.info(f"⚠️  Verificaciones con advertencia: {self.checks_failed}\n")

        if self.checks_failed == 0:
            logger.info("🎉 TODA LA CONFIGURACIÓN ESTÁ OK\n")
            logger.info("PRÓXIMOS PASOS:")
            logger.info("1. Ver IPs asignadas por DHCP (ISP1 e ISP2)")
            logger.info("2. Configurar balanceo de carga (ver DUAL_ISP_LOADBALANCE.md)")
            logger.info("3. Conectar APs a puertos 3-5")
            logger.info("4. Conectar dispositivos a puertos 6-7")
            logger.info("5. Iniciar Sistema NAC: python -m uvicorn app.main:app")
            return True
        else:
            logger.info("⚠️  REVISAR ADVERTENCIAS ARRIBA\n")
            return False

    def disconnect(self):
        if self.ssh:
            self.ssh.close()

def main():
    router_ip = os.getenv("ROUTER_IP", "192.168.88.1")
    router_user = os.getenv("ROUTER_USER", "admin")
    router_password = os.getenv("ROUTER_PASSWORD", "")

    if not router_password:
        logger.error("❌ ROUTER_PASSWORD no definida en .env")
        return False

    verifier = RouterVerifier(router_ip, router_user, router_password)

    try:
        if not verifier.connect():
            return False

        return verifier.verify_all()
    finally:
        verifier.disconnect()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
