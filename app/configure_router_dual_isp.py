#!/usr/bin/env python3
"""
Script para configurar automáticamente MikroTik con Dual ISP + APs + Balanceo de Carga

Requisitos:
- paramiko (SSH)
- Sistema NAC ya instalado

Uso:
    python app/configure_router_dual_isp.py
"""

import sys
import time
import logging
from pathlib import Path
import paramiko
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RouterConfigurator:
    """Configura MikroTik con Dual ISP automáticamente"""

    def __init__(self, host, user, password, ssh_port=22):
        self.host = host
        self.user = user
        self.password = password
        self.ssh_port = ssh_port
        self.ssh = None

    def connect(self):
        """Conecta al router via SSH"""
        try:
            logger.info(f"Conectando a {self.host}...")
            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh.connect(
                self.host,
                port=self.ssh_port,
                username=self.user,
                password=self.password,
                timeout=10
            )
            logger.info("✅ Conectado al router")
            return True
        except Exception as e:
            logger.error(f"❌ Error conectando: {e}")
            return False

    def disconnect(self):
        """Desconecta del router"""
        if self.ssh:
            self.ssh.close()
            logger.info("Desconectado del router")

    def execute_command(self, command):
        """Ejecuta comando en el router"""
        try:
            stdin, stdout, stderr = self.ssh.exec_command(command)
            output = stdout.read().decode()
            error = stderr.read().decode()
            return output, error
        except Exception as e:
            logger.error(f"Error ejecutando comando: {e}")
            return None, str(e)

    def backup_config(self):
        """Hace backup de la configuración actual"""
        try:
            logger.info("📦 Haciendo backup de configuración...")
            sftp = self.ssh.open_sftp()

            # Crear backup
            output, error = self.execute_command("/export file=backup_before_nac")
            time.sleep(1)

            # Descargar backup
            sftp.get("backup_before_nac.rsc", "backup_before_nac.rsc")
            logger.info("✅ Backup guardado: backup_before_nac.rsc")

            sftp.close()
            return True
        except Exception as e:
            logger.error(f"❌ Error haciendo backup: {e}")
            return False

    def upload_script(self, script_path):
        """Sube script al router"""
        try:
            logger.info(f"📤 Subiendo script: {script_path}")
            sftp = self.ssh.open_sftp()
            sftp.put(str(script_path), "setup_dual_isp.rsc")
            sftp.close()
            logger.info("✅ Script subido")
            return True
        except Exception as e:
            logger.error(f"❌ Error subiendo script: {e}")
            return False

    def apply_config(self):
        """Aplica la configuración desde el script"""
        try:
            logger.info("⚙️ Aplicando configuración...")
            output, error = self.execute_command("/import setup_dual_isp.rsc")

            if error and "failure" in error.lower():
                logger.error(f"❌ Error en configuración: {error}")
                return False

            logger.info("✅ Configuración aplicada")
            time.sleep(2)
            return True
        except Exception as e:
            logger.error(f"❌ Error aplicando config: {e}")
            return False

    def verify_interfaces(self):
        """Verifica interfaces configuradas"""
        try:
            logger.info("🔍 Verificando interfaces...")
            output, _ = self.execute_command("/interface print")

            expected = ["ether1-isp1", "ether2-isp2", "ether3-ap", "ether4-ap", "ether5-ap"]

            for iface in expected:
                if iface in output:
                    logger.info(f"   ✅ {iface}")
                else:
                    logger.warning(f"   ⚠️ {iface} no encontrada")

            return True
        except Exception as e:
            logger.error(f"❌ Error verificando: {e}")
            return False

    def verify_bridges(self):
        """Verifica bridges configurados"""
        try:
            logger.info("🔍 Verificando bridges...")
            output, _ = self.execute_command("/interface bridge print")

            expected = ["bridge-isp1", "bridge-isp2", "bridge-aps", "bridge-lan"]

            for bridge in expected:
                if bridge in output:
                    logger.info(f"   ✅ {bridge}")
                else:
                    logger.warning(f"   ⚠️ {bridge} no encontrada")

            return True
        except Exception as e:
            logger.error(f"❌ Error verificando bridges: {e}")
            return False

    def verify_dhcp(self):
        """Verifica servidores DHCP"""
        try:
            logger.info("🔍 Verificando DHCP...")
            output, _ = self.execute_command("/ip dhcp-server print")

            expected = ["dhcp-aps", "dhcp-lan"]

            for dhcp in expected:
                if dhcp in output:
                    logger.info(f"   ✅ {dhcp}")
                else:
                    logger.warning(f"   ⚠️ {dhcp} no encontrada")

            return True
        except Exception as e:
            logger.error(f"❌ Error verificando DHCP: {e}")
            return False

    def verify_rest_api(self):
        """Verifica REST API habilitada"""
        try:
            logger.info("🔍 Verificando REST API...")
            output, _ = self.execute_command("/ip service print")

            if "rest" in output.lower() and "enabled" in output.lower():
                logger.info("   ✅ REST API habilitada")
                return True
            else:
                logger.warning("   ⚠️ REST API podría no estar habilitada")
                return False
        except Exception as e:
            logger.error(f"❌ Error verificando REST API: {e}")
            return False

    def verify_api_user(self):
        """Verifica usuario API creado"""
        try:
            logger.info("🔍 Verificando usuario API...")
            output, _ = self.execute_command("/user print")

            if "api-container" in output:
                logger.info("   ✅ Usuario api-container creado")
                return True
            else:
                logger.warning("   ⚠️ Usuario api-container no encontrado")
                return False
        except Exception as e:
            logger.error(f"❌ Error verificando usuario: {e}")
            return False

    def wait_for_dhcp(self, timeout=60):
        """Espera a que DHCP asigne IPs"""
        logger.info("⏳ Esperando a que DHCP asigne IPs (esto puede tomar 30-60 segundos)...")

        start_time = time.time()
        isp1_assigned = False
        isp2_assigned = False

        while time.time() - start_time < timeout:
            try:
                output, _ = self.execute_command("/ip dhcp-client print")

                if "dhcp-isp1" in output and "bound" in output:
                    isp1_assigned = True
                    logger.info("   ✅ ISP1 obtuvo IP")

                if "dhcp-isp2" in output and "bound" in output:
                    isp2_assigned = True
                    logger.info("   ✅ ISP2 obtuvo IP")

                if isp1_assigned and isp2_assigned:
                    return True

                time.sleep(5)
            except:
                time.sleep(5)

        logger.warning("⏳ Timeout esperando DHCP. Verifica manualmente:")
        logger.warning("   /ip dhcp-client print")
        return False

    def show_dhcp_status(self):
        """Muestra estado de DHCP"""
        try:
            logger.info("📊 Estado de direcciones IP:")
            output, _ = self.execute_command("/ip address print")
            logger.info(output)
        except Exception as e:
            logger.error(f"Error: {e}")

    def show_next_steps(self):
        """Muestra próximos pasos"""
        logger.info("\n" + "="*70)
        logger.info("🎉 CONFIGURACIÓN COMPLETADA")
        logger.info("="*70)
        logger.info("\n📋 PRÓXIMOS PASOS:")
        logger.info("\n1. Verificar IPs asignadas por DHCP:")
        logger.info("   En el navegador: http://192.168.88.1")
        logger.info("   O via SSH: /ip address print")
        logger.info("\n2. Configurar Balanceo de Carga (PCC):")
        logger.info("   - Anotar IPs gateway de ISP1 e ISP2")
        logger.info("   - Ver docs/DUAL_ISP_LOADBALANCE.md para instrucciones")
        logger.info("   - Ejecutar comandos de Mangle y Rutas")
        logger.info("\n3. Conectar APs:")
        logger.info("   - Puerto 3: AP1 (VLAN 100: 192.168.100.0/24)")
        logger.info("   - Puerto 4: AP2 (VLAN 100: 192.168.100.0/24)")
        logger.info("   - Puerto 5: AP3 (VLAN 100: 192.168.100.0/24)")
        logger.info("\n4. Conectar Dispositivos LAN:")
        logger.info("   - Puerto 6: Switches/Devices (VLAN 200: 192.168.88.0/24)")
        logger.info("   - Puerto 7: PC Gerencia (VLAN 200: 192.168.88.0/24)")
        logger.info("\n5. Iniciar Sistema NAC:")
        logger.info("   python -m uvicorn app.main:app --reload")
        logger.info("\n6. Acceder a dashboard:")
        logger.info("   http://localhost:8080")
        logger.info("\n" + "="*70)


def main():
    """Función principal"""

    logger.info("🚀 MikroTik Dual ISP Configurator")
    logger.info("="*70)

    # Obtener credenciales de .env
    router_ip = os.getenv("ROUTER_IP", "192.168.88.1")
    router_user = os.getenv("ROUTER_USER", "admin")
    router_password = os.getenv("ROUTER_PASSWORD", "")

    if not router_password:
        logger.error("❌ ROUTER_PASSWORD no definida en .env")
        return False

    logger.info(f"📍 Router: {router_ip}")
    logger.info(f"👤 Usuario: {router_user}")

    # Buscar script
    script_path = Path("routeros/router_setup_dual_isp.rsc")
    if not script_path.exists():
        logger.error(f"❌ Script no encontrado: {script_path}")
        return False

    # Crear configurador
    config = RouterConfigurator(router_ip, router_user, router_password)

    try:
        # Conectar
        if not config.connect():
            return False

        # Backup
        config.backup_config()

        # Subir script
        if not config.upload_script(script_path):
            return False

        # Aplicar configuración
        if not config.apply_config():
            return False

        # Verificaciones
        logger.info("\n🔍 VERIFICANDO CONFIGURACIÓN:")
        config.verify_interfaces()
        config.verify_bridges()
        config.verify_dhcp()
        config.verify_rest_api()
        config.verify_api_user()

        # Esperar DHCP
        logger.info("")
        config.wait_for_dhcp()

        # Mostrar estado
        config.show_dhcp_status()

        # Próximos pasos
        config.show_next_steps()

        return True

    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return False
    finally:
        config.disconnect()


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n⚠️ Cancelado por usuario")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Error inesperado: {e}")
        sys.exit(1)
