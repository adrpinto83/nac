# 🆘 Troubleshooting - Solución de Problemas

## Instalación

### "Python no reconocido" en Windows

**Problema:** Command 'python' is not recognized

**Soluciones:**
1. Verificar que Python está en PATH:
   ```bash
   python --version
   ```
   
2. Si no funciona, reinstalar Python:
   - Descargar desde python.org
   - ✅ **Marcar "Add Python to PATH"**
   - Reiniciar CMD después

3. Usar `python3` en lugar de `python`:
   ```bash
   python3 --version
   ```

### "venv no se activa" en Windows

**Problema:** `venv\Scripts\activate` no funciona

**Soluciones:**
```bash
# Si estás en PowerShell, cambiar a CMD
cmd

# O ejecutar:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Luego:
venv\Scripts\Activate.ps1
```

### "ModuleNotFoundError: No module named 'fastapi'"

**Problema:** Las dependencias no se instalaron correctamente

**Soluciones:**
```bash
# 1. Verificar que el ambiente virtual está activado
# Debe verse (venv) en el prompt

# 2. Reinstalar dependencias
pip install --upgrade pip
pip install -r requirements.txt

# 3. Verificar instalación
pip list | grep fastapi
```

---

## Configuración

### "ConnectionRefusedError: [Errno 111] Connection refused"

**Problema:** No puede conectarse al router

**Causas posibles:**
1. Router IP incorrecto en `.env`
2. REST API no habilitada en router
3. Firewall bloqueando puerto 80
4. Router apagado o desconectado

**Soluciones:**
```bash
# 1. Verificar IP del router
ping 192.168.88.1

# 2. Verificar que REST API está habilitada en router
# En WebFig: IP > Services > REST API

# 3. Verificar conexión
curl http://192.168.88.1/rest/system/identity

# 4. Actualizar .env con IP correcta
nano .env
```

### "Invalid credentials" / "401 Unauthorized"

**Problema:** Error de autenticación con router

**Causas:**
1. Usuario `api-container` no existe
2. Contraseña incorrecta
3. Usuario sin permisos

**Soluciones:**
```bash
# 1. Ejecutar script de configuración del router
python app/configure_router.py

# 2. Verificar usuario manualmente en router:
# En WebFig: System > Users > api-container
# Verificar grupo: write

# 3. Actualizar .env con credenciales correctas
# ROUTER_USER=api-container
# ROUTER_PASSWORD=tu_contraseña
```

---

## Base de Datos

### "sqlite3.OperationalError: unable to open database file"

**Problema:** BD no se puede abrir

**Soluciones:**
```bash
# 1. Crear carpeta data si no existe
mkdir data

# 2. Verificar permisos
# En Linux: chmod 755 data/

# 3. Reiniciar aplicación
```

### "database is locked"

**Problema:** La BD está siendo usada por otro proceso

**Soluciones:**
```bash
# 1. Esperar unos segundos y reintentar

# 2. Si persiste, reiniciar aplicación
# Ctrl+C en la terminal
python -m uvicorn app.main:app --reload

# 3. En Linux, buscar procesos:
lsof | grep db.sqlite3
kill -9 <pid>
```

---

## Aplicación

### "Port 8080 already in use"

**Problema:** Puerto 8080 ya está siendo usado

**Soluciones:**
```bash
# 1. Usar otro puerto
python -m uvicorn app.main:app --port 8081

# 2. En Windows, encontrar qué usa el puerto:
netstat -ano | findstr :8080

# 3. Matar el proceso (reemplazar PID):
taskkill /PID <PID> /F

# 4. En Linux:
lsof -i :8080
kill -9 <PID>
```

### "Application startup error"

**Problema:** La aplicación falla al iniciar

**Soluciones:**
```bash
# 1. Ver error completo en consola
python -m uvicorn app.main:app --reload

# 2. Verificar .env está configurado
cat .env

# 3. Verificar BD existe
ls -la data/

# 4. Ver logs detallados
python -m uvicorn app.main:app --reload --log-level debug
```

### "scheduler not initialized"

**Problema:** Scheduler falla en startup

**Soluciones:**
```bash
# 1. Instalar APScheduler
pip install apscheduler

# 2. Verificar conexión con router
# Health check debe funcionar

# 3. Ver logs del scheduler
# Búscar "Scheduler" en la salida
```

---

## Frontend

### "Cannot GET /" o página en blanco

**Problema:** El frontend no carga

**Soluciones:**
```bash
# 1. Verificar que la API está corriendo
curl http://localhost:8080/health

# 2. Verificar que los archivos estáticos existen
ls -la static/

# 3. Limpiar caché del navegador
# Ctrl+Shift+Delete y limpiar cookies

# 4. Abrir consola del navegador (F12)
# Ver si hay errores en la consola
```

### "Login fallido" o "Invalid credentials"

**Problema:** Login no funciona

**Causas:**
1. Usuario no existe en BD
2. Contraseña incorrecta
3. BD vacía

**Soluciones:**
```bash
# 1. Verificar que el usuario existe
sqlite3 data/db.sqlite3 "SELECT * FROM users;"

# 2. Si no hay usuarios, crear uno manualmente
# Opción A: Via script
python scripts/create_admin_user.py

# Opción B: Via SQL directamente
sqlite3 data/db.sqlite3
INSERT INTO users (username, password_hash, full_name, role) 
VALUES ('admin', 'hash', 'Admin', 'SUPERADMIN');
```

### "API endpoints retornan 404"

**Problema:** Los endpoints no existen

**Soluciones:**
```bash
# 1. Verificar que la API está corriendo en puerto 8080
curl http://localhost:8080/health

# 2. Actualizar BASE_URL en js/api.js si es necesario
# const API_BASE = 'http://localhost:8080/api'

# 3. Verificar CORS en main.py
# CORSMiddleware debe permitir tu dominio
```

---

## Router

### "Router health check failed"

**Problema:** El router no responde

**Soluciones:**
```bash
# 1. Ping al router
ping 192.168.88.1

# 2. Verificar que REST API está habilitada
# WebFig > IP > Services > REST API (puerto 80)

# 3. Verificar firewall del router no bloquea
# WebFig > IP > Firewall > Filter Rules

# 4. Reiniciar servicio REST API del router
# WebFig > System > Packages, buscar "rest-api"
```

### "No devices detected" en ARP sync

**Problema:** Scheduler no sincroniza dispositivos

**Soluciones:**
```bash
# 1. Verificar que hay dispositivos en la red
# Ping a alguna IP en el rango 192.168.88.x

# 2. Verificar tabla ARP en router
# WebFig > IP > ARP

# 3. Ver logs del scheduler
# Búscar "ARP sync" en los logs

# 4. Ejecutar ARP sync manualmente
# Ver sección de desarrollo
```

---

## Performance

### "Dashboard lento" o "API response lenta"

**Problema:** Aplicación responde lentamente

**Soluciones:**
```bash
# 1. Verificar BD no está corrupta
sqlite3 data/db.sqlite3 "PRAGMA integrity_check;"

# 2. Limpiar datos antiguos manualmente
sqlite3 data/db.sqlite3 "DELETE FROM traffic_snapshots WHERE timestamp < datetime('now', '-30 days');"

# 3. Aumentar workers en producción
gunicorn app.main:app --workers 4

# 4. Ver logs de queries lentas
python -m uvicorn app.main:app --reload --log-level debug
```

### "Alto uso de memoria"

**Problema:** Proceso Python usa mucha RAM

**Soluciones:**
```bash
# 1. Reducir intervalo de cleanup
# En app/config.py: TRAFFIC_SYNC_INTERVAL = 600

# 2. Reducir límite de datos guardados
# En app/scheduler/tasks.py: days=7 (de 30)

# 3. Usar limite de memoria en Docker
# docker run -m 512m miktotik-nac:latest
```

---

## Logs & Debugging

### Ver logs detallados

```bash
# Windows
python -m uvicorn app.main:app --reload --log-level debug

# Linux/macOS
python -m uvicorn app.main:app --reload --log-level debug 2>&1 | tee app.log
```

### Ver logs del Scheduler

```bash
# Buscar en logs:
grep "Scheduler" app.log
grep "Health check" app.log
grep "ARP sync" app.log
```

### Debuggear API call

```bash
# En js/api.js, descomentar logs
console.log("Calling:", url);
console.log("Response:", response);

# O usar curl desde terminal
curl -H "Authorization: Bearer TOKEN" http://localhost:8080/api/users/
```

---

## Reinstalación Completa

Si todo falla, reinstalar limpio:

```bash
# 1. Desactivar ambiente virtual
deactivate  # o venv\Scripts\deactivate.bat en Windows

# 2. Eliminar ambiente y BD
rm -rf venv data/db.sqlite3

# 3. Recrear ambiente
python -m venv venv
source venv/bin/activate  # o venv\Scripts\activate en Windows

# 4. Reinstalar
pip install -r requirements.txt

# 5. Copiar .env
cp .env.example .env
# Editar con credenciales correctas

# 6. Iniciar
python -m uvicorn app.main:app --reload
```

---

## Soporte Adicional

Si el problema persiste:

1. **Ver logs completos:** Copiar todo lo que aparece en la consola
2. **Verificar .env:** Confirmar que todos los valores son correctos
3. **Verificar router:** Confirmar que REST API está habilitada
4. **Ver documentación:** 
   - ARQUITECTURA.md
   - SCHEDULER.md
   - ROUTEROS_CLIENT.md

**Contacto:** Si necesitas ayuda adicional, consultar la documentación técnica.
