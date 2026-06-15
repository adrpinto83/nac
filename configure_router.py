#!/usr/bin/env python3
"""
Script de configuración remota del router MikroTik vía SSH.
Ejecuta: python configure_router.py
"""

import subprocess
import sys
import time
from pathlib import Path

class RouterConfigurator:
    def __init__(self, router_ip="192.168.88.1", router_user="admin", router_pass=""):
        self.router_ip = router_ip
        self.router_user = router_user
        self.router_pass = router_pass
        # Usar el script simplificado
        self.script_file = Path(__file__).parent / "router_setup_simple.rsc"
        if not self.script_file.exists():
            self.script_file = Path(__file__).parent / "router_setup.rsc"

    def check_ssh_available(self):
        """Verifica si SSH/SCP están disponibles en el sistema"""
        try:
            subprocess.run(["ssh", "-V"], capture_output=True, timeout=5)
            subprocess.run(["scp", "-V"], capture_output=True, timeout=5)
            return True
        except FileNotFoundError:
            return False

    def upload_script(self):
        """Carga el script .rsc al router vía SCP"""
        print("[*] Cargando script a router vía SCP...")
        cmd = [
            "scp",
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null",
            str(self.script_file),
            f"{self.router_user}@{self.router_ip}:/router_setup.rsc"
        ]

        try:
            # Usar 'sshpass' si la contraseña está disponible
            if self.router_pass:
                cmd = ["sshpass", "-p", self.router_pass] + cmd
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            else:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                print("✓ Script cargado exitosamente")
                return True
            else:
                print(f"✗ Error al cargar script: {result.stderr}")
                return False

        except FileNotFoundError:
            print("✗ SSH/SCP no disponible. Instala openssh-client (Linux/Mac) o Git Bash (Windows)")
            return False
        except subprocess.TimeoutExpired:
            print("✗ Timeout en conexión SSH")
            return False

    def execute_script(self):
        """Ejecuta el script en el router vía SSH"""
        print("[*] Ejecutando script en el router...")
        cmd = [
            "ssh",
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null",
            f"{self.router_user}@{self.router_ip}",
            "/import file-name=router_setup.rsc"
        ]

        try:
            if self.router_pass:
                cmd = ["sshpass", "-p", self.router_pass] + cmd
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            else:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

            print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)

            if result.returncode == 0:
                print("✓ Script ejecutado exitosamente")
                return True
            else:
                print(f"✗ Error al ejecutar script (código {result.returncode})")
                return False

        except subprocess.TimeoutExpired:
            print("✗ Timeout ejecutando script (>2 minutos)")
            return False

    def verify_connectivity(self):
        """Verifica conectividad con el router vía REST API"""
        print("\n[*] Verificando conectividad con REST API...")
        try:
            import httpx
            client = httpx.Client(
                auth=(self.router_user, self.router_pass or "admin"),
                verify=False,
                timeout=10.0
            )
            response = client.get(f"http://{self.router_ip}:80/rest/system/identity")
            if response.status_code == 200:
                print(f"✓ REST API accesible: {response.json()}")
                client.close()
                return True
            else:
                print(f"✗ REST API retornó {response.status_code}")
                client.close()
                return False
        except Exception as e:
            print(f"✗ No se pudo verificar REST API: {e}")
            print("  (Instala httpx: pip install httpx)")
            return False

    def run(self):
        """Ejecuta el flujo completo de configuración"""
        print("\n" + "="*70)
        print("MikroTik NAC System — Configurador Remoto")
        print("="*70 + "\n")

        print(f"[*] Configurando router en: {self.router_ip}")
        print(f"[*] Usuario: {self.router_user}\n")

        # Verificar script
        if not self.script_file.exists():
            print(f"✗ Script no encontrado: {self.script_file}")
            return False

        # Verificar SSH
        if not self.check_ssh_available():
            print("⚠ SSH no disponible en tu sistema.")
            print("\nOPCIONES:")
            print("1. Linux/Mac: instala openssh-client (apt-get install openssh-client)")
            print("2. Windows: instala Git Bash (https://git-scm.com/download/win)")
            print("3. Windows: instala WSL (Windows Subsystem for Linux)")
            print("4. Alternativa: copia manualmente el script router_setup.rsc a la terminal del router")
            print("\nPara opción manual:")
            print("  a) Abre terminal del router en WebFig (System > Console)")
            print("  b) Copia el contenido de router_setup.rsc")
            print("  c) Pega en la terminal")
            return False

        # Cargar script
        if not self.upload_script():
            print("\n⚠ No se pudo cargar el script vía SCP.")
            print("Alternativa manual:")
            print("  1. Abre la terminal del router (WebFig o SSH)")
            print("  2. Ejecuta: /import file-name=router_setup.rsc")
            return False

        # Ejecutar script
        time.sleep(1)
        if not self.execute_script():
            print("\n✗ Fallo la ejecución del script")
            return False

        # Esperar y verificar
        print("\n[*] Esperando que el router complete la configuración (30 segundos)...")
        time.sleep(30)

        # Verificar conectividad
        if not self.verify_connectivity():
            print("\n⚠ No se pudo verificar la conectividad.")
            print("Espera 1-2 minutos y verifica manualmente:")
            print("  curl -u api-container:NAC_MikroTik_2025 http://192.168.88.1:80/rest/system/identity")

        print("\n" + "="*70)
        print("✓ CONFIGURACIÓN COMPLETADA")
        print("="*70)
        print("\nPróximos pasos:")
        print("1. Conecta la PC al router (WiFi 'DS-1405-PDVSA' o cable)")
        print("2. Ejecuta la aplicación NAC: python main.py")
        print("3. Abre http://localhost:8080 en el navegador")
        print("="*70 + "\n")

        return True


if __name__ == "__main__":
    import os

    # Configuración (puedes editar aquí)
    ROUTER_IP = os.getenv("ROUTER_IP", "192.168.88.1")
    ROUTER_USER = os.getenv("ROUTER_USER", "admin")
    ROUTER_PASS = os.getenv("ROUTER_PASS", "")  # Deja vacío si la contraseña es vacía

    # Ejecutar
    configurator = RouterConfigurator(
        router_ip=ROUTER_IP,
        router_user=ROUTER_USER,
        router_pass=ROUTER_PASS
    )

    success = configurator.run()
    sys.exit(0 if success else 1)
