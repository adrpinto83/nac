#!/usr/bin/env python3
"""
Script para configurar automáticamente Balanceo de Carga (PCC)

Requiere que DHCP haya asignado IPs a ISP1 e ISP2
"""

import sys
import os
import paramiko
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class LoadBalanceConfigurator:
    def __init__(self, host, user, password):
        self.host = host
        self.user = user
        self.password = password
        self.ssh = None
        self.isp1_gateway = None
        self.isp2_gateway = None

    def connect(self):
        try:
            logger.info(f"🔌 Conectando a {self.host}...")
            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh.connect(self.host, username=self.user, password=self.password, timeout=10)
            logger.info("✅ Conectado\n")
            return True
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            return False

    def execute(self, cmd):
        try:
            _, stdout, stderr = self.ssh.exec_command(cmd)
            return stdout.read().decode(), stderr.read().decode()
        except Exception as e:
            return None, str(e)

    def get_isp_gateways(self):
        """Obtiene IPs gateway asignadas por DHCP"""
        logger.info("🔍 Obteniendo IPs de ISPs desde DHCP...\n")

        output, _ = self.execute("/ip dhcp-client print detail")

        lines = output.split('\n')
        for i, line in enumerate(lines):
            if 'dhcp-isp1' in line:
                # Buscar la línea con gateway
                for j in range(i, min(i+10, len(lines))):
                    if 'gateway=' in lines[j]:
                        parts = lines[j].split('gateway=')
                        if len(parts) > 1:
                            self.isp1_gateway = parts[1].split()[0]
                            logger.info(f"📍 ISP1 Gateway: {self.isp1_gateway}")

            elif 'dhcp-isp2' in line:
                for j in range(i, min(i+10, len(lines))):
                    if 'gateway=' in lines[j]:
                        parts = lines[j].split('gateway=')
                        if len(parts) > 1:
                            self.isp2_gateway = parts[1].split()[0]
                            logger.info(f"📍 ISP2 Gateway: {self.isp2_gateway}")

        if not self.isp1_gateway or not self.isp2_gateway:
            logger.warning("⚠️  No se encontraron gateways DHCP")
            logger.info("\nVerifica manualmente:")
            logger.info("  ssh admin@192.168.88.1")
            logger.info("  /ip dhcp-client print detail")
            return False

        logger.info("")
        return True

    def configure_mangle_rules(self):
        """Configura reglas de Mangle para PCC"""
        logger.info("🔧 Configurando Mangle rules...\n")

        commands = [
            # Limpiar rutas anteriores
            "/ip route remove [find dst-address=0.0.0.0/0]",

            # Agregar Mangle rules
            "/ip firewall mangle add chain=prerouting dst-address-type=!local new-routing-mark=isp1 passthrough=yes per-connection-classifier=both-addresses-and-ports:2/0 comment='PCC to ISP1'",
            "/ip firewall mangle add chain=prerouting dst-address-type=!local new-routing-mark=isp2 passthrough=yes per-connection-classifier=both-addresses-and-ports:2/1 comment='PCC to ISP2'",

            # Agregar rutas
            f"/ip route add dst-address=0.0.0.0/0 gateway={self.isp1_gateway} routing-mark=isp1 comment='Route ISP1' distance=10",
            f"/ip route add dst-address=0.0.0.0/0 gateway={self.isp2_gateway} routing-mark=isp2 comment='Route ISP2' distance=10",

            # Ruta default como fallback
            f"/ip route add dst-address=0.0.0.0/0 gateway={self.isp1_gateway} comment='Default route' distance=20",
        ]

        for cmd in commands:
            logger.info(f"  Ejecutando: {cmd[:60]}...")
            output, error = self.execute(cmd)
            if error and "failure" in error.lower():
                logger.error(f"  ❌ Error: {error}")
                return False

        logger.info("✅ Mangle rules configuradas\n")
        return True

    def verify_configuration(self):
        """Verifica que el balanceo está configurado"""
        logger.info("🔍 Verificando configuración...\n")

        # Verificar Mangle rules
        output, _ = self.execute("/ip firewall mangle print")
        if "isp1" in output and "isp2" in output:
            logger.info("✅ Mangle rules activas")
        else:
            logger.warning("⚠️  Mangle rules no se ven")

        # Verificar rutas
        output, _ = self.execute("/ip route print")
        if self.isp1_gateway in output and self.isp2_gateway in output:
            logger.info("✅ Rutas configuradas")
        else:
            logger.warning("⚠️  Rutas no se ven completamente")

        logger.info("")
        return True

    def show_summary(self):
        """Muestra resumen de configuración"""
        logger.info("=" * 60)
        logger.info("BALANCEO DE CARGA CONFIGURADO")
        logger.info("=" * 60 + "\n")

        logger.info("📊 CONFIGURACIÓN:")
        logger.info(f"  ISP1 Gateway: {self.isp1_gateway}")
        logger.info(f"  ISP2 Gateway: {self.isp2_gateway}\n")

        logger.info("🔄 BALANCEO (PCC):")
        logger.info("  Conexiones pares -> ISP1")
        logger.info("  Conexiones impares -> ISP2\n")

        logger.info("🛣️  RUTAS:")
        logger.info(f"  Routing Mark isp1 -> {self.isp1_gateway}")
        logger.info(f"  Routing Mark isp2 -> {self.isp2_gateway}")
        logger.info(f"  Default -> {self.isp1_gateway}\n")

        logger.info("✅ PRÓXIMOS PASOS:")
        logger.info("  1. Probar conectividad: ping 8.8.8.8")
        logger.info("  2. Ver tráfico: /interface monitor-traffic ether1-isp1")
        logger.info("  3. Ver estadísticas: /ip firewall mangle print stats")
        logger.info("  4. Iniciar Sistema NAC")
        logger.info("")

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

    config = LoadBalanceConfigurator(router_ip, router_user, router_password)

    try:
        if not config.connect():
            return False

        if not config.get_isp_gateways():
            return False

        if not config.configure_mangle_rules():
            return False

        config.verify_configuration()
        config.show_summary()

        return True
    finally:
        config.disconnect()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
