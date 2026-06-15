# Configuración del Router MikroTik — Guía Paso a Paso

Este documento explica cómo limpiar y configurar tu router MikroTik hAP ac3 desde cero para el sistema NAC.

## ⚠️ ADVERTENCIA

Esta configuración **limpiará completamente** las siguientes secciones del router:
- Reglas de firewall (filter, nat, mangle)
- Address-lists (whitelist, blocklist)
- Simple Queues
- Entradas DNS estáticas
- DHCP server
- Configuración wireless

**NO borrará:**
- Interfaces físicas ni sus IPs
- Usuario admin
- Certificados
- Backups

**Recomendación:** Realiza un backup antes de empezar:
```
/system backup make name=backup-pre-nac
```

---

## OPCIÓN 1: Configuración automática vía SSH (Recomendado)

### Requisitos previos:
1. **SSH habilitado en el router** (por defecto está habilitado)
2. **Acceso SSH disponible en tu PC:**
   - **Linux/Mac:** `ssh -V` debe funcionar
   - **Windows:** Instala Git Bash (https://git-scm.com/download/win) O activa WSL
   - **Windows (alternativa):** Instala PuTTY o MobaXterm

### Pasos:

```bash
# 1. Abre una terminal en el directorio del proyecto
cd /home/adrpinto/miktotik

# 2. (Opcional) Si el router requiere contraseña para admin:
export ROUTER_PASS="tu_contraseña_admin"

# 3. Ejecuta el configurador
python3 configure_router.py
```

**Salida esperada:**
```
[*] Cargando script a router vía SCP...
✓ Script cargado exitosamente
[*] Ejecutando script en el router...
... (logs del router) ...
✓ Script ejecutado exitosamente
[*] Esperando que el router complete la configuración (30 segundos)...
[*] Verificando conectividad con REST API...
✓ REST API accesible: {'name': 'hAP ac3', ...}

✓ CONFIGURACIÓN COMPLETADA
```

---

## OPCIÓN 2: Configuración manual vía Terminal Web (WebFig)

### Pasos:

1. **Abre el navegador** y ve a `http://192.168.88.1:80`
   - Login con usuario `admin` (sin contraseña o tu contraseña)
   - Navega a **System > Console** (o **Terminal** si aparece directamente)

2. **Abre la terminal de RouterOS** (se abre una ventana negra)

3. **Copia y pega lo siguiente línea por línea** (o todo de una vez):
   ```
   /import file-name=router_setup.rsc
   ```

   > Si `router_setup.rsc` no existe en el router:
   > - Descarga `router_setup.rsc` de esta carpeta
   > - Cárgalo al router vía FTP (dirección: `192.168.88.1`, usuario: `admin`)
   > - Luego ejecuta `/import file-name=router_setup.rsc`

4. **Espera a que termine** (~30 segundos). Verás logs como:
   ```
   FASE 1: Limpiando configuración antigua...
   - Removiendo reglas de firewall...
   - Removiendo address-lists...
   ... (más logs) ...
   ✓ CONFIGURACIÓN COMPLETADA
   ```

---

## OPCIÓN 3: Configuración manual vía SSH desde terminal

Si tienes SSH en tu PC:

```bash
# 1. Conecta al router por SSH
ssh admin@192.168.88.1

# 2. Una vez dentro, copia y pega el contenido de router_setup.rsc
# O, carga el archivo:
scp router_setup.rsc admin@192.168.88.1:/
ssh admin@192.168.88.1 '/import file-name=router_setup.rsc'
```

---

## Verificación después de la configuración

### Test 1: Verificar REST API desde tu PC

**En Bash/PowerShell:**
```bash
# Linux/Mac/Git Bash
curl -u api-container:NAC_MikroTik_2025 http://192.168.88.1:80/rest/system/identity

# PowerShell (Windows)
$user = "api-container"
$pass = "NAC_MikroTik_2025"
$base64 = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("${user}:${pass}"))
$headers = @{"Authorization" = "Basic $base64"}
Invoke-RestMethod -Uri "http://192.168.88.1:80/rest/system/identity" -Headers $headers
```

**Respuesta esperada:**
```json
{
  "name": "hAP ac3",
  "platform": "hAP ac3",
  ".id": "*1"
}
```

### Test 2: Verificar configuración en el router

En la terminal del router:
```routeros
# Ver firewall rules
/ip firewall filter print where chain=forward

# Ver address-lists
/ip firewall address-list print

# Ver DHCP server
/ip dhcp-server print

# Ver wireless
/interface wireless print
```

### Test 3: Conectarse a la WiFi

1. En tu PC, busca la red WiFi `DS-1405-PDVSA` (aparecerá como red disponible pero sin mostrar nombre)
2. Conecta sin contraseña (red abierta)
3. Deberías obtener una IP en el rango `192.168.88.100-200` vía DHCP
4. Verifica en el router: `/ip dhcp-server lease print`

---

## Solución de problemas

### Error: "connection refused" al hacer curl
- Verifica que la REST API está habilitada: `/ip service print`
- Verifica que el puerto 80 está en la configuración: `/ip service set rest disabled=no port=80`
- Reinicia el servicio: `/ip service enable rest` y `/ip service disable rest`

### Error: "401 Unauthorized"
- Usuario o contraseña incorrectos
- Verifica que `api-container` existe: `/user print`
- Verifica contraseña: `/user set api-container password=NAC_MikroTik_2025`

### WiFi no aparece
- Verifica que la interfaz wireless está habilitada: `/interface wireless print where name=wlan1`
- Si está deshabilitada: `/interface wireless set [find name=wlan1] disabled=no`

### DHCP no asigna IPs
- Verifica que el pool existe: `/ip pool print`
- Verifica que el servidor DHCP está activo: `/ip dhcp-server print`
- Verifica la red DHCP: `/ip dhcp-server network print`

### Script falla (import error)
- Revisa los logs: `/log print`
- Intenta copiar y pegar **cada sección** del script manualmente
- O ejecuta línea por línea ignorando la que falla

---

## Reversión: Restaurar backup anterior

Si algo sale mal y hiciste backup:

```routeros
/system backup restore name=backup-pre-nac
```

El router se reiniciará automáticamente.

---

## Configuración completada ✓

Una vez pasadas todas las verificaciones, el router está listo para que la aplicación NAC funcione.

### Próximos pasos:
1. Ve al **Entregable 2** en la documentación principal
2. Instala dependencias de la aplicación Python
3. Ejecuta `python main.py` en tu PC
4. Abre `http://localhost:8080` en el navegador

---

## Notas importantes

- **Usuario API:** `api-container` / `NAC_MikroTik_2025` (configurable en el script)
- **REST API:** `http://192.168.88.1:80/rest`
- **SSID WiFi:** `DS-1405-PDVSA` (oculto)
- **DHCP Pool:** `192.168.88.100-200`
- **Gateway:** `192.168.88.1`
- **DNS:** `8.8.8.8, 8.8.4.4` (configurable)

Si necesitas cambiar estas valores, edita `router_setup.rsc` antes de ejecutarlo.
