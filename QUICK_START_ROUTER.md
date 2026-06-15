# 🚀 Configuración del Router — Quick Start

## 3 opciones para configurar el router MikroTik:

### ✨ OPCIÓN A: Automática (Recomendado) — 1 minuto

```bash
python3 configure_router.py
```

> Requiere: SSH disponible en tu PC
> - Linux/Mac: ya incluido
> - Windows: Git Bash o WSL

**Qué hace:**
1. Sube el script `router_setup.rsc` al router
2. Lo ejecuta automáticamente
3. Espera 30 segundos
4. Verifica que está funcionando

---

### 📋 OPCIÓN B: Manual vía WebFig (Navegador) — 2 minutos

1. Abre http://192.168.88.1:80 en tu navegador
2. Login (usuario: `admin`, password: vacío o tu contraseña)
3. Ve a **System > Console** (o busca Terminal)
4. En la terminal negra, pega esto:
   ```
   /import file-name=router_setup.rsc
   ```
5. Espera 30 segundos a que termine

> Si dice "file not found", carga primero `router_setup.rsc` al router vía FTP

---

### 💻 OPCIÓN C: Manual vía SSH (Terminal) — 2 minutos

```bash
# 1. Conecta por SSH
ssh admin@192.168.88.1

# 2. Ejecuta el script
/import file-name=router_setup.rsc

# 3. Espera 30 segundos
```

---

## ✅ Verificar que funcionó

Elige una:

### Test 1: Script de validación (recomendado)
```bash
python3 validate_router.py
```

Verás un reporte completo de la configuración.

### Test 2: Simple con curl
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
  ".id": "*1"
}
```

---

## 📊 Qué se configuró

| Componente | Valor |
|---|---|
| **Usuario API** | `api-container` / `NAC_MikroTik_2025` |
| **REST API** | `http://192.168.88.1:80/rest` |
| **SSID WiFi** | `DS-1405-PDVSA` (oculto, abierto) |
| **DHCP** | `192.168.88.100-200` |
| **Firewall** | Whitelist/Blocklist de MACs |
| **DNS** | Bloqueador estático configurado |

---

## 🔧 Solución rápida de problemas

**"Connection refused"**
```bash
# Verifica que REST API está habilitada
curl http://192.168.88.1:80/rest/system/identity
```

**"401 Unauthorized"**
- Usuario/contraseña incorrectos
- Por defecto: `api-container` / `NAC_MikroTik_2025`

**WiFi no aparece**
- Espera 30 segundos después de configurar
- Verifica en el router: `/interface wireless print`

**DHCP no da IPs**
- `/ip dhcp-server print` (debe mostrar DHCP activo)
- `/ip dhcp-server network print` (red DHCP configurada)

---

## 📚 Información detallada

Para más detalles, ver `ROUTER_SETUP.md`

---

## 🎯 Próximo paso

Una vez que el router esté configurado:

1. **Entregable 2:** Estructura del proyecto Python
2. **Entregable 3:** Cliente RouterOS
3. ... y más

Continúa en la documentación principal.

---

**¿Listo?** 👉 Ejecuta una de las opciones de arriba
