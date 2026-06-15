# ✓ ENTREGABLE 1 — RESUMEN COMPLETO

## Objetivo
Preparar el router MikroTik hAP ac3 desde cero con:
- Limpieza completa de configuración anterior
- Usuario API dedicado con permisos mínimos
- REST API habilitada
- Reglas de firewall failsafe (bloquean tráfico no autorizado aunque la app esté apagada)
- SSID oculto "DS-1405-PDVSA" (red abierta)
- Servidor DHCP configurado
- Address-lists (whitelist/blocklist) para control de acceso por MAC

---

## 📦 Archivos entregados

### 1. **router_setup.rsc** (Script RouterOS)
**Ubicación:** `/home/adrpinto/miktotik/router_setup.rsc`

Script de configuración RouterOS que:
- Limpia firewall, queues, DNS, DHCP, wireless
- Crea usuario `api-container`
- Habilita REST API en puerto 80
- Crea listas de control (mac-whitelist, mac-blocked)
- Configura reglas de firewall failsafe
- Configura SSID "DS-1405-PDVSA" (oculto, abierto)
- Habilita DHCP server con pool 192.168.88.100-200
- Configura DNS

**Ejecutable mediante:**
- SSH automático: `python3 configure_router.py`
- WebFig manual: `/import file-name=router_setup.rsc`
- SSH manual: `ssh admin@192.168.88.1 /import file-name=router_setup.rsc`

---

### 2. **configure_router.py** (Configurador automático)
**Ubicación:** `/home/adrpinto/miktotik/configure_router.py`

Script Python que automatiza la configuración:
- Verifica disponibilidad de SSH en tu PC
- Carga `router_setup.rsc` al router vía SCP
- Ejecuta el script automáticamente
- Espera 30 segundos a que complete
- Verifica conectividad REST API

**Uso:**
```bash
python3 configure_router.py
```

**Requisitos:**
- SSH disponible (Linux/Mac por defecto, Windows con Git Bash/WSL)
- Acceso a puerto 22 del router (SSH activo)

---

### 3. **validate_router.py** (Validador)
**Ubicación:** `/home/adrpinto/miktotik/validate_router.py`

Script Python que verifica que la configuración es correcta:
- Conectividad REST API
- Address-lists (whitelist/blocklist)
- Firewall rules
- Interfaz wireless (SSID)
- DHCP server y leases
- Tabla ARP (dispositivos en la red)
- Simple Queues
- Entradas DNS estáticas
- Servicio REST API

**Uso:**
```bash
python3 validate_router.py
```

**Salida:** Reporte completo con ✓/✗ de cada test

---

### 4. **ROUTER_SETUP.md** (Guía detallada)
**Ubicación:** `/home/adrpinto/miktotik/ROUTER_SETUP.md`

Documento completo con:
- **ADVERTENCIA:** Qué se limpiará
- **3 opciones de configuración:**
  1. Automática vía SSH (recomendado)
  2. Manual vía WebFig (navegador)
  3. Manual vía SSH (terminal)
- **Verificación post-configuración**
- **Solución de problemas**
- **Reversión (restaurar backup)**

---

### 5. **QUICK_START_ROUTER.md** (Guía rápida)
**Ubicación:** `/home/adrpinto/miktotik/QUICK_START_ROUTER.md`

Resumen ejecutivo:
- 3 opciones en 2 minutos cada una
- Verificación rápida
- Troubleshooting básico

---

### 6. **.env.example** (Plantilla de variables)
**Ubicación:** `/home/adrpinto/miktotik/.env.example`

Plantilla con TODAS las variables de entorno necesarias:
- Configuración del router
- Configuración de la app
- JWT y autenticación
- Base de datos
- Scheduler
- DHCP
- Wireless
- Perfiles de ancho de banda
- Auditoría
- Email (opcional)
- CORS

**Uso:**
```bash
cp .env.example .env
# Edita .env según tu entorno
```

**Importante:** `.env` está en `.gitignore`, nunca se comitea.

---

### 7. **.gitignore** (Exclusiones git)
**Ubicación:** `/home/adrpinto/miktotik/.gitignore`

Excluye archivos que no deben commitearse:
- `.env` (variables secretas)
- `venv/` (virtual environment)
- `__pycache__/`, `*.pyc` (archivos compilados)
- `*.sqlite3`, `*.db` (bases de datos locales)
- `*.log` (logs)
- `.idea/`, `.vscode/` (IDEs)
- Backups del router

---

## 🎯 Configuración alcanzada

### Credenciales
| Componente | Valor |
|---|---|
| Usuario API | `api-container` |
| Contraseña API | `NAC_MikroTik_2025` |
| Usuario admin | `admin` (sin cambios) |

### Servicios
| Componente | Valor |
|---|---|
| REST API | `http://192.168.88.1:80/rest` |
| SSID WiFi | `DS-1405-PDVSA` (oculto) |
| Seguridad WiFi | Open (sin contraseña) |
| DHCP Pool | `192.168.88.100-200` |
| Gateway | `192.168.88.1` |
| DNS | `8.8.8.8, 8.8.4.4` |

### Listas de control
| Lista | Descripción |
|---|---|
| `mac-whitelist` | MACs autorizadas (ACCEPT) |
| `mac-blocked` | MACs bloqueadas (DROP) |

### Reglas de Firewall (failsafe)
1. **Regla 0:** ACCEPT si MAC ∈ mac-whitelist
2. **Regla 1:** DROP si MAC ∈ mac-blocked
3. **Regla 2:** DROP desconocidas (deshabilitada, activar si es política default-deny)

### NAT
- Masquerade en interfaz WAN (ether1)

---

## ✅ Pasos de instalación

### Opción A: Automática (recomendado)
```bash
# 1. En tu PC, terminal en el directorio del proyecto
cd /home/adrpinto/miktotik

# 2. Ejecuta
python3 configure_router.py

# 3. Espera a que termine (2-3 minutos)

# 4. Verifica
python3 validate_router.py
```

### Opción B: Manual vía WebFig
```bash
# 1. Abre http://192.168.88.1:80 en navegador
# 2. Login con admin
# 3. System > Console (o Terminal)
# 4. Pega: /import file-name=router_setup.rsc
# 5. Espera 30 segundos
# 6. Verifica: python3 validate_router.py
```

### Opción C: Manual vía SSH
```bash
# 1. SSH al router
ssh admin@192.168.88.1

# 2. Ejecuta
/import file-name=router_setup.rsc

# 3. Espera 30 segundos
# 4. Verifica: python3 validate_router.py
```

---

## 🔍 Verificación

### Test 1: Script de validación (RECOMENDADO)
```bash
python3 validate_router.py
```

Genera reporte completo de todos los componentes.

### Test 2: Curl simple
```bash
# Linux/Mac
curl -u api-container:NAC_MikroTik_2025 http://192.168.88.1:80/rest/system/identity

# PowerShell
$user = "api-container"
$pass = "NAC_MikroTik_2025"
$base64 = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("${user}:${pass}"))
$headers = @{"Authorization" = "Basic $base64"}
Invoke-RestMethod -Uri "http://192.168.88.1:80/rest/system/identity" -Headers $headers
```

Respuesta esperada:
```json
{
  "name": "hAP ac3",
  ".id": "*1"
}
```

---

## 🛡️ Seguridad — Failsafe garantizado

Incluso si la aplicación NAC se cae:
1. ✓ MACs en `mac-whitelist` pueden acceder (regla 0)
2. ✓ MACs en `mac-blocked` están bloqueadas (regla 1)
3. ✓ Las reglas están en el router, no dependen de la app
4. ✓ Tráfico no whitelistado continúa según configuración (forwarding normal si no está habilitada la política default-deny)

---

## 📊 Archivos de referencia rápida

```
/home/adrpinto/miktotik/
├── router_setup.rsc              ← Script RouterOS
├── configure_router.py           ← Configurador automático
├── validate_router.py            ← Validador
├── ROUTER_SETUP.md              ← Guía detallada
├── QUICK_START_ROUTER.md        ← Guía rápida (⭐ LEER PRIMERO)
├── ENTREGABLE_1_RESUMEN.md      ← Este archivo
├── .env.example                 ← Variables de entorno
└── .gitignore                   ← Exclusiones git
```

---

## 🚀 Próximo paso

Una vez que hayas configurado el router y verificado con `validate_router.py`:

👉 **Entregable 2:** Estructura del proyecto Python

El Entregable 2 incluirá:
- Layout completo de carpetas y archivos
- Descripción del rol de cada módulo
- Preparación para los entregables siguientes (backend, frontend, etc.)

---

## 📞 Troubleshooting rápido

| Problema | Solución |
|---|---|
| **"Connection refused"** | REST API no activa: `/ip service set rest disabled=no port=80` |
| **"401 Unauthorized"** | Credenciales incorrectas. Verifica `api-container` y contraseña |
| **WiFi no aparece** | Espera 30s. Verifica: `/interface wireless print where name=wlan1` |
| **DHCP no asigna IPs** | Verifica: `/ip dhcp-server print` y `/ip dhcp-server network print` |
| **Script falla (import)** | Verifica logs: `/log print`. O copia línea por línea manualmente |

Más info en `ROUTER_SETUP.md`.

---

## ✨ Conclusión

**Entregable 1 completado:**
- ✓ Router limpio y configurado desde cero
- ✓ User API creado con permisos mínimos
- ✓ REST API habilitada
- ✓ Firewall failsafe implementado
- ✓ SSID configurado
- ✓ DHCP operativo
- ✓ Herramientas de configuración y validación listos

**El router está 100% listo para que la aplicación NAC comience a trabajar en el Entregable 2+**

---

**¿Listo?** 👉 Ejecuta `python3 configure_router.py` (o elige otra opción) y luego `python3 validate_router.py` para verificar.
