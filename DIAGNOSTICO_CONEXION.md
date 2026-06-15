# 🔍 Diagnóstico de Conectividad - Router MikroTik

Si no puedes conectarte al router en `192.168.88.1`, usa esta guía para diagnosticar el problema.

## 🚀 Ejecutar Diagnóstico

### En tu PC:

**Linux/macOS:**
```bash
bash diagnostico_router.sh
```

**Windows (PowerShell):**
```powershell
bash diagnostico_router.sh
```

El script verificará automáticamente:
- ✅ Tu IP local
- ✅ Ping al router
- ✅ Puertos SSH y REST API
- ✅ Conexión SSH

---

## 🎯 Problemas Comunes y Soluciones

### Problema 1: "Ping: Host Unreachable"

**Causa:** El router no está en la misma red que tu PC

**Soluciones:**

1. **Verificar IP de tu PC:**
   ```bash
   # Linux/macOS
   ifconfig | grep inet
   
   # Windows
   ipconfig /all
   ```
   
   Debe verse algo como: `192.168.88.x` (donde x = 1-254)

2. **Si tu IP NO es 192.168.88.x:**
   - El router está en una red diferente
   - Necesitas encontrar la IP correcta del router
   - Busca "Default Gateway" en tu configuración de red

3. **Verificar conexión de red:**
   - ¿Estás conectado por WiFi?
   - ¿O por Ethernet?
   - ¿El cable está conectado?

4. **Reconectar a la red:**
   - Desconéctate del WiFi
   - Espera 10 segundos
   - Reconéctate

---

### Problema 2: "Ping OK pero SSH Falla"

**Causa:** SSH no está habilitado en el router

**Soluciones:**

1. **Habilitar SSH en WebFig:**
   ```
   1. Abrir navegador: http://192.168.88.1
   2. Ir a: System > SSH Server
   3. Verificar que "Enabled" está marcado
   4. Hacer click en Apply
   ```

2. **Verificar puerto SSH:**
   ```bash
   # Debe estar en puerto 22 (por defecto)
   # En WebFig: System > SSH Server > Port
   ```

3. **Si aún falla, reiniciar router:**
   - Apagar 30 segundos
   - Encender
   - Esperar a que inicie (2-3 minutos)
   - Intentar nuevamente

---

### Problema 3: "REST API No Responde"

**Causa:** REST API no está habilitada en el router

**Soluciones:**

1. **Habilitar REST API:**
   ```
   1. Abrir navegador: http://192.168.88.1
   2. Ir a: IP > Services
   3. Buscar "rest"
   4. Verificar que está "enabled"
   5. Verificar puerto: debe ser 80
   ```

2. **Desde SSH:**
   ```bash
   ssh admin@192.168.88.1
   
   # En el router:
   /ip service print
   /ip service enable rest
   /ip service set rest port=80
   ```

---

## 🆔 Encontrar IP Real del Router

Si el router **no está en 192.168.88.1**:

### Opción 1: Desde tu PC

```bash
# Linux/macOS - Ver gateway por defecto
netstat -rn | grep default

# Otra forma
route -n | grep default
```

### Opción 2: Desde WebFig

```
1. En tu navegador, ir a: http://192.168.0.1 (o similar)
2. Buscar "System > Identity"
3. Ver la IP actual
```

### Opción 3: Desde tu router

```bash
# Si puedes acceder al router de otra forma:
ssh admin@<ip-router>
/ip address print
```

### Opción 4: Buscar en la red

```bash
# Linux/macOS - Ver todos los dispositivos en la red
arp -a | grep -i mikrotik

# O usar nmap (si está instalado)
nmap -sn 192.168.1.0/24
```

---

## ✅ Una Vez Encontrada la IP Correcta

1. **Editar .env:**
   ```bash
   nano .env
   ```

2. **Buscar la línea:**
   ```ini
   ROUTER_IP=192.168.88.1
   ```

3. **Cambiar a la IP correcta:**
   ```ini
   ROUTER_IP=192.168.1.1
   # (o la IP que encontraste)
   ```

4. **Guardar y salir:**
   - nano: `Ctrl+X`, `Y`, `Enter`
   - vim: `:wq`, `Enter`

5. **Intentar conexión nuevamente:**
   ```bash
   bash ejecutar_todo.sh
   ```

---

## 🧪 Verificaciones Manuales

### Probar Ping

```bash
# Windows
ping 192.168.88.1

# Linux/macOS
ping -c 4 192.168.88.1
```

### Probar SSH

```bash
ssh admin@192.168.88.1

# O con contraseña específica
ssh -p 22 admin@192.168.88.1
```

### Probar REST API

```bash
# Con curl
curl http://192.168.88.1/rest/system/identity

# Con navegador
http://192.168.88.1
```

---

## 🔧 Reiniciar Router

Si nada funciona, reinicia el router:

1. **Apagar:**
   - Desconectar poder del router
   - Esperar 30 segundos

2. **Encender:**
   - Conectar poder nuevamente
   - Esperar 3-5 minutos

3. **Verificar estado:**
   - Todos los LEDs deben estar prendidos
   - WiFi debe estar activo
   - Intentar ping: `ping 192.168.88.1`

---

## 📊 Estado Esperado

Una vez conectado correctamente, deberías ver:

```bash
$ bash diagnostico_router.sh

✅ Tu IP: 192.168.88.X
✅ Ping al router: 0% packet loss
✅ Puerto SSH (22): ABIERTO
✅ Puerto REST API (80): ABIERTO
✅ Conexión SSH: EXITOSA
```

---

## 🚨 Si Aún No Funciona

1. **Captura los resultados del diagnóstico**
2. **Toma nota del error específico**
3. **Verifica:**
   - Que el router está encendido
   - Que WiFi está visible
   - Que tienes internet
   - Que puedes acceder a http://192.168.88.1 en navegador

4. **Opciones adicionales:**
   - Resetear router (botón reset)
   - Reinstalar firmware MikroTik
   - Contactar soporte MikroTik

---

## 💡 Tips Útiles

- **WebFig es más rápido que SSH** para cambios rápidos
- **Siempre guardar cambios** en WebFig (Apply button)
- **Reiniciar después de cambios importantes**
- **Anotar la contraseña** por si la cambias

---

**Una vez que la conexión funcione, ejecuta:**
```bash
bash ejecutar_todo.sh
```

¡El resto es automático! 🚀
