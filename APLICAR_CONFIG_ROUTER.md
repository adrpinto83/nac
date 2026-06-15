# 🚀 Aplicar Configuración del Router Automáticamente

Guía rápida para configurar el MikroTik con Dual ISP automáticamente.

## ⚡ Instalación Rápida (5 minutos)

### Paso 1: Verificar Requisitos

```bash
# Verificar Python 3
python3 --version  # Debe ser 3.9+

# Verificar que estás en la carpeta del proyecto
ls -la app/configure_router_dual_isp.py
```

### Paso 2: Configurar Variables de Entorno

```bash
# Copiar template
cp .env.example .env

# Editar con credenciales del router
nano .env
# (o vim .env en Linux/macOS)
```

**Editar estas líneas:**

```ini
ROUTER_IP=192.168.88.1           # IP actual del router
ROUTER_PORT=22                   # Puerto SSH
ROUTER_USER=admin                # Usuario MikroTik
ROUTER_PASSWORD=contraseña       # Contraseña actual

# También verificar estas:
DEBUG=False
LOG_LEVEL=INFO
```

**Guardar y salir:**
- nano: `Ctrl+X`, `Y`, `Enter`
- vim: `:wq`, `Enter`

### Paso 3: Ejecutar Script de Configuración

#### Windows (PowerShell)

```powershell
# Instalar dependencia
pip install paramiko

# Ejecutar script
python app/configure_router_dual_isp.py
```

#### Linux/macOS (Bash)

```bash
# Hacer script ejecutable
chmod +x apply_router_config.sh

# Ejecutar
./apply_router_config.sh
```

O directamente:

```bash
pip install paramiko
python3 app/configure_router_dual_isp.py
```

### Paso 4: Confirmar Operación

El script te pedirá confirmación:

```
⚠️  ADVERTENCIA:
Esta operación:
  1. Hará un BACKUP de la configuración actual
  2. LIMPIARÁ la configuración existente
  3. Aplicará la nueva configuración Dual ISP

¿Deseas continuar? (s/n)
```

**Escribe `s` y presiona Enter**

## 📊 Qué Hace el Script

```
✅ Se conecta al router via SSH
✅ Hace BACKUP de configuración actual
✅ Sube script de configuración
✅ Limpia configuración anterior
✅ Aplica nueva configuración
✅ Habilita REST API
✅ Crea usuario api-container
✅ Configura bridges y DHCP
✅ Espera a que DHCP asigne IPs
✅ Verifica que todo funcione
```

## ⏱️ Duración Esperada

- Conexión SSH: 5 segundos
- Backup: 10 segundos
- Aplicar config: 30 segundos
- Esperar DHCP: 30-60 segundos
- Verificación: 10 segundos

**Total: 2-3 minutos**

## 📋 Output Esperado

```
🚀 MikroTik Dual ISP Configurator
======================================================================
📍 Router: 192.168.88.1
👤 Usuario: admin
✅ Conectado al router
📦 Haciendo backup de configuración...
✅ Backup guardado: backup_before_nac.rsc
📤 Subiendo script: routeros/router_setup_dual_isp.rsc
✅ Script subido
⚙️ Aplicando configuración...
✅ Configuración aplicada

🔍 VERIFICANDO CONFIGURACIÓN:
🔍 Verificando interfaces...
   ✅ ether1-isp1
   ✅ ether2-isp2
   ✅ ether3-ap
   ✅ ether4-ap
   ✅ ether5-ap
🔍 Verificando bridges...
   ✅ bridge-isp1
   ✅ bridge-isp2
   ✅ bridge-aps
   ✅ bridge-lan
🔍 Verificando DHCP...
   ✅ dhcp-aps
   ✅ dhcp-lan
🔍 Verificando REST API...
   ✅ REST API habilitada
🔍 Verificando usuario API...
   ✅ Usuario api-container creado

⏳ Esperando a que DHCP asigne IPs...
   ✅ ISP1 obtuvo IP
   ✅ ISP2 obtuvo IP

📊 Estado de direcciones IP:
[Listado de IPs asignadas]

======================================================================
🎉 CONFIGURACIÓN COMPLETADA
======================================================================
```

## ⚙️ Próximos Pasos Después de la Configuración

### 1. Verificar IPs de ISPs

```bash
# Via SSH al router
ssh admin@192.168.88.1

# Ver IPs asignadas
/ip address print

# Buscar las IPs de:
# - dhcp-isp1 -> anotar gateway
# - dhcp-isp2 -> anotar gateway
```

### 2. Configurar Balanceo de Carga (PCC)

Ver **[DUAL_ISP_LOADBALANCE.md](docs/DUAL_ISP_LOADBALANCE.md)** para:
- Obtener IPs gateway de ISPs
- Configurar Mangle rules
- Crear rutas con balanceo

**Ejemplo (reemplaza IPs):**

```bash
# En SSH del router
/ip firewall mangle add chain=prerouting dst-address-type=!local \
    new-routing-mark=isp1 passthrough=yes \
    per-connection-classifier=both-addresses-and-ports:2/0

/ip firewall mangle add chain=prerouting dst-address-type=!local \
    new-routing-mark=isp2 passthrough=yes \
    per-connection-classifier=both-addresses-and-ports:2/1

# Reemplazar <IP_ISP1_GATEWAY> y <IP_ISP2_GATEWAY>
/ip route add dst-address=0.0.0.0/0 gateway=<IP_ISP1_GATEWAY> routing-mark=isp1
/ip route add dst-address=0.0.0.0/0 gateway=<IP_ISP2_GATEWAY> routing-mark=isp2
```

### 3. Conectar Access Points

```
Puerto 3 → AP1 (VLAN 100: 192.168.100.0/24)
Puerto 4 → AP2 (VLAN 100: 192.168.100.0/24)
Puerto 5 → AP3 (VLAN 100: 192.168.100.0/24)
```

Los APs obtendrán IP automáticamente vía DHCP.

### 4. Conectar Dispositivos LAN

```
Puerto 6 → Switches/Devices (VLAN 200: 192.168.88.0/24)
Puerto 7 → PC Gerencia (VLAN 200: 192.168.88.0/24)
```

### 5. Iniciar Sistema NAC

```bash
# En tu PC (no en el router)
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

### 6. Acceder al Dashboard

```
http://localhost:8080
```

**Login:**
- Usuario: admin
- Contraseña: (que creaste en BD)

## 🆘 Troubleshooting

### "Error: Connection refused"

**Causa:** No se puede conectar al router

**Soluciones:**
```bash
# 1. Verificar IP es correcta
ping 192.168.88.1

# 2. Verificar SSH está habilitado en router
# En WebFig: System > SSH Server (debe estar enabled)

# 3. Verificar credenciales en .env
cat .env | grep ROUTER_
```

### "Error: Authentication failed"

**Causa:** Usuario o contraseña incorrectos

**Soluciones:**
```bash
# 1. Verificar usuario existe en router
ssh admin@192.168.88.1
# Debería conectar sin problemas

# 2. Resetear contraseña si es necesario
# Por WebFig > System > Users
```

### "DHCP timeout"

**Causa:** Los módems no están conectados o no responden

**Soluciones:**
```bash
# 1. Conectar ambos módems a puertos 1 y 2
# 2. Verificar que tienen internet

# 3. Esperar más (hasta 2 minutos)
# 4. Revisar manualmente en router:
ssh admin@192.168.88.1
/ip dhcp-client print
```

### "REST API no se ve habilitada"

**Solucionar:**
```bash
ssh admin@192.168.88.1
/ip service enable rest
/ip service set rest port=80
/ip service print
```

## 📊 Estado del Router Después

```
INTERFACES:
├─ ether1-isp1: DHCP (IP de ISP1)
├─ ether2-isp2: DHCP (IP de ISP2)
├─ ether3-ap: bridge-aps (192.168.100.0/24)
├─ ether4-ap: bridge-aps (192.168.100.0/24)
├─ ether5-ap: bridge-aps (192.168.100.0/24)
├─ ether6-lan: bridge-lan (192.168.88.1)
└─ ether7-gerencia: bridge-lan (192.168.88.1)

SERVICIOS:
├─ REST API: Puerto 80 (habilitado)
├─ SSH: Puerto 22
├─ HTTP: Puerto 80 (NAC)
└─ DHCP: Habilitado para APs y LAN

USUARIOS:
├─ admin: Usuario MikroTik estándar
└─ api-container: Usuario para NAC System

DHCP SERVERS:
├─ dhcp-aps: 192.168.100.2-254
└─ dhcp-lan: 192.168.88.10-254
```

## ✅ Checklist Final

- [ ] Script ejecutado exitosamente
- [ ] Backup guardado (backup_before_nac.rsc)
- [ ] Ambos ISPs tienen IP asignada
- [ ] Balanceo de carga configurado
- [ ] APs conectadas a puertos 3-5
- [ ] Dispositivos LAN en puertos 6-7
- [ ] REST API accesible en puerto 80
- [ ] Usuario api-container creado
- [ ] Sistema NAC iniciado
- [ ] Dashboard accesible en http://localhost:8080

## 🔄 Si Necesitas Revertir

```bash
# 1. Restaurar backup guardado
ssh admin@192.168.88.1
/import backup_before_nac.rsc

# 2. O restaurar manualmente desde WebFig
# Files > Seleccionar backup_before_nac.rsc > Import
```

---

**¡Tu router está listo para el Sistema NAC!** 🎉

Para más detalles técnicos, ver:
- [DUAL_ISP_LOADBALANCE.md](docs/DUAL_ISP_LOADBALANCE.md)
- [INSTALACION.md](INSTALACION.md)
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
